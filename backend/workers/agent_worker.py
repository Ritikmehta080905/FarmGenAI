"""
backend/workers/agent_worker.py

Asynchronous worker daemon that consumes negotiation jobs from Redis Stream
and executes them via the LangGraph state machine (graph_orchestrator).

Architecture:
  Redis Stream  →  agent_worker.py  →  graph_orchestrator  →  ChromaDB/DB
  Redis Pub/Sub ←─────────────────────────────────────────────────────────
"""

import sys
import os
import asyncio
import json
import logging
from datetime import datetime, timezone

# Ensure project root is in PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import redis.asyncio as aioredis
from config.settings import REDIS_URL
from database.db import init_db, Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AgentWorker")

STREAM_KEY = "agri:negotiation:jobs"
CONSUMER_GROUP = "worker_group"
CONSUMER_NAME = "worker_1"
TELEMETRY_CHANNEL = "agri:telemetry:updates"


def _build_initial_state(payload: dict, neg_id: str) -> dict:
    """
    Convert the raw negotiation payload from the API into a NegotiationState
    compatible dict for the LangGraph graph_orchestrator.
    """
    market_price = float(payload.get("market_price", 0) or 0)
    min_price = float(payload.get("min_price", 0) or 0)
    if market_price == 0:
        market_price = min_price * 1.15  # fallback estimate

    return {
        "crop": payload.get("crop", "Unknown"),
        "quantity": float(payload.get("quantity", 100)),
        "min_price": min_price,
        "target_price": float(payload.get("target_price", min_price * 1.2) or min_price * 1.2),
        "spoilage_days": int(payload.get("spoilage_days", 7) or 7),
        "location": payload.get("location", "Market"),
        "market_price": market_price,
        "round": 0,
        "max_rounds": int(payload.get("max_rounds", 6) or 6),
        "history": [],
        "buyer_profile": None,
        "logs": [f"🚀 [Worker] Negotiation {neg_id} dispatched via Redis Stream."],
        "status": "ACTIVE",
        "proposed_scenario": "direct-sale",
        "next_action": "start",
        "deal": None,
        "plan": None,
        "reflection": None,
        "selected_buyer": None,
        "market_offers": [],
        "user_id": payload.get("user_id"),
        "latest_farmer_ask": None,
        "latest_buyer_offer": None,
        "buyers_list": payload.get("buyers_list", []),
        "rag_context": None,
        "market_intelligence": None,
        "recommendation": None,
    }


def _serialize_result(final_state: dict, neg_id: str) -> dict:
    """
    Convert the final LangGraph state into the negotiation result dict
    that gets stored in the database and broadcast via WebSocket.
    """
    deal = final_state.get("deal") or {}
    final_price = deal.get("price") or final_state.get("latest_buyer_offer")

    return {
        "negotiation_id": neg_id,
        "user_id": final_state.get("user_id"),
        "crop": final_state.get("crop"),
        "quantity": final_state.get("quantity"),
        "status": final_state.get("status", "UNKNOWN"),
        "final_price": final_price,
        "deal": deal,
        "selected_buyer": final_state.get("selected_buyer"),
        "market_offers": final_state.get("market_offers", []),
        "logs": final_state.get("logs", []),
        "history": final_state.get("history", []),
        "plan": final_state.get("plan"),
        "reflection": final_state.get("reflection"),
        "recommendation": final_state.get("recommendation"),
        "market_intelligence": final_state.get("market_intelligence"),
        "rounds": final_state.get("round", 0),
        "summary": (
            f"Deal at ₹{final_price}/kg with {deal.get('buyer_name', 'Unknown')}"
            if final_state.get("status") == "DEAL"
            else f"Escalated to {final_state.get('status', 'UNKNOWN').lower()}"
        ),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }


async def run_worker():
    logger.info("🚀 AgentWorker initializing...")
    await init_db()

    logger.info(f"Connecting to Redis at {REDIS_URL}...")
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

    # Import graph AFTER DB is initialized to avoid circular imports
    from backend.agents.graph_orchestrator import graph_orchestrator

    # Ensure consumer group exists
    try:
        await redis_client.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
        logger.info(f"Consumer group '{CONSUMER_GROUP}' created on stream '{STREAM_KEY}'.")
    except Exception:
        pass  # Group already exists

    logger.info("✅ AgentWorker ready. Listening for negotiation jobs...")

    while True:
        try:
            jobs = await redis_client.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={STREAM_KEY: ">"},
                count=1,
                block=2000,
            )

            if not jobs:
                await asyncio.sleep(0.1)
                continue

            stream_name, messages = jobs[0]
            for msg_id, data in messages:
                payload = json.loads(data.get("payload", "{}"))
                neg_id = data.get("neg_id", "unknown")
                logger.info(f"📥 Processing negotiation job: {neg_id}")

                async def publish(event_type: str, event_data: dict):
                    await redis_client.publish(
                        TELEMETRY_CHANNEL,
                        json.dumps({
                            "negotiation_id": neg_id,
                            "event": {"type": event_type, "data": event_data},
                        }),
                    )

                try:
                    # Publish start signal
                    await publish("status_update", {"message": f"🔄 LangGraph started for {neg_id}"})

                    # Build NegotiationState from payload
                    initial_state = _build_initial_state(payload, neg_id)

                    # Run LangGraph in thread pool (it's synchronous)
                    loop = asyncio.get_running_loop()
                    final_state = await loop.run_in_executor(
                        None,
                        lambda: graph_orchestrator.invoke(initial_state)
                    )

                    # Serialize and persist the result
                    result = _serialize_result(final_state, neg_id)
                    Database.update_negotiation(neg_id, result)

                    # Publish log lines
                    for log_line in final_state.get("logs", []):
                        await publish("status_update", {"message": log_line})

                    # Publish final outcome
                    await publish("negotiation_finished", result)
                    logger.info(f"✅ Negotiation {neg_id} completed. Status: {result['status']}")

                except Exception as e:
                    logger.error(f"❌ Error in negotiation {neg_id}: {e}", exc_info=True)
                    error_result = {
                        "negotiation_id": neg_id,
                        "status": "FAILED",
                        "error": str(e),
                        "logs": [f"❌ Worker error: {e}"],
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                    }
                    Database.update_negotiation(neg_id, error_result)
                    await publish("negotiation_failed", {"error": str(e)})

                # Acknowledge processed message
                await redis_client.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)

        except Exception as e:
            logger.error(f"Worker loop error: {e}", exc_info=True)
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("AgentWorker terminated by user.")
