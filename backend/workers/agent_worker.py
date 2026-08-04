"""
backend/workers/agent_worker.py

Asynchronous worker daemon consuming negotiation jobs from Redis Stream
and executing them via the LangGraph state machine.
"""

import sys
import os
import asyncio
import json
import logging

# Ensure project root is in PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import redis.asyncio as aioredis
from config.settings import REDIS_URL
from database.db import init_db
from backend.services.negotiation_service import NegotiationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AgentWorker")


async def run_worker():
    logger.info("Initializing Database connection...")
    await init_db()
    
    logger.info(f"Connecting to Redis Stream at {REDIS_URL}...")
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    
    # Initialize Negotiation Service instance
    service = NegotiationService()

    # Ensure Redis Stream group exists
    try:
        await redis_client.xgroup_create("agri:negotiation:jobs", "worker_group", id="0", mkstream=True)
        logger.info("Created consumer group 'worker_group' on stream 'agri:negotiation:jobs'.")
    except Exception:
        # Group already exists
        pass

    logger.info("Worker started successfully. Listening for job notifications...")
    
    while True:
        try:
            # Read jobs from stream
            jobs = await redis_client.xreadgroup(
                groupname="worker_group",
                consumername="worker_1",
                streams={"agri:negotiation:jobs": ">"},
                count=1,
                block=2000
            )
            
            if not jobs:
                await asyncio.sleep(0.2)
                continue

            stream_name, messages = jobs[0]
            for msg_id, data in messages:
                payload = json.loads(data["payload"])
                neg_id = data["neg_id"]
                logger.info(f"📥 Picked up negotiation job {neg_id} from stream.")

                # Publisher function for live updates
                async def publish_progress(event):
                    event_payload = {
                        "negotiation_id": neg_id,
                        "event": event
                    }
                    await redis_client.publish("agri:telemetry:updates", json.dumps(event_payload))

                loop = asyncio.get_running_loop()
                
                # Wrap progress callbacks
                def sync_callback(event):
                    asyncio.run_coroutine_threadsafe(publish_progress(event), loop)

                try:
                    result = await loop.run_in_executor(
                        None,
                        lambda: service.start_negotiation(
                            payload,
                            scenario="direct-sale",
                            pre_id=neg_id,
                            live_event_callback=sync_callback
                        )
                    )
                    
                    # Publish final negotiation outcome
                    final_payload = {
                        "negotiation_id": neg_id,
                        "event": {
                            "type": "negotiation_finished",
                            "data": result
                        }
                    }
                    await redis_client.publish("agri:telemetry:updates", json.dumps(final_payload))
                    logger.info(f"✅ Finished negotiation job {neg_id} successfully.")
                    
                except Exception as e:
                    logger.error(f"❌ Error executing negotiation job {neg_id}: {e}")
                    error_payload = {
                        "negotiation_id": neg_id,
                        "event": {
                            "type": "negotiation_failed",
                            "data": {"error": str(e)}
                        }
                    }
                    await redis_client.publish("agri:telemetry:updates", json.dumps(error_payload))

                # Acknowledge the message in Redis
                await redis_client.xack("agri:negotiation:jobs", "worker_group", msg_id)

        except Exception as e:
            logger.error(f"Error in main worker loop: {e}")
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker daemon terminated by user.")
