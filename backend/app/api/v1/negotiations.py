import json
import logging
import asyncio
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from backend.app.core.deps import get_current_active_user
from backend.app.core.redis import redis_manager
from backend.app.core.controllers import negotiation_controller
from backend.models.negotiation_model import StartNegotiationRequest
from database.db import Database
from backend.repositories.user_repository import UserRepository
from nodes.node_hub import hub
from backend.websocket.agent_updates import agent_update_hub

router = APIRouter()
logger = logging.getLogger("backend.api.negotiations")
_executor = ThreadPoolExecutor(max_workers=10)

async def _run_negotiation_bg(payload: dict, neg_id: str):
    """Run the blocking negotiation in a thread-pool, then push WS events."""
    loop = asyncio.get_running_loop()

    async def _broadcast_progress_event(event: dict):
        event_type = event.get("type")
        data = event.get("data", {})
        message = None
        agent_type = None
        offer = None

        if event_type == "offer_made":
            offer = data.get("price")
            message = data.get("message") or f"Opening offer at Rs.{offer}/kg"
            agent_type = "farmer"
        elif event_type == "counter_offer":
            offer = data.get("price")
            message = data.get("message") or f"Counter offer at Rs.{offer}/kg"
            agent_name = str(data.get("agent", "")).lower()
            farmer_name = str(payload.get("farmer_name", "")).lower()
            agent_type = "farmer" if farmer_name and farmer_name in agent_name else "buyer"
        elif event_type == "agreement":
            offer = data.get("price")
            qty = data.get("quantity")
            message = f"Deal reached at Rs.{offer}/kg for {qty}kg"
        elif event_type == "storage":
            message = data.get("message") or "🏗️ Warehouse node joined. Temporary storage available."
            agent_type = "warehouse"
        elif event_type == "processing":
            message = data.get("message") or "⚙️ Industrial Processor joined. Alternative channel active."
            agent_type = "processor"
        elif event_type == "compost":
            message = data.get("message") or "♻️ Ecological Agent joined. Zero-waste fallback active."
            agent_type = "compost"
        elif event_type == "status_update":
            message = data.get("message") or "Market conditions analyzed."
            agent_type = "system"
        elif event_type == "scenario_ready":
             agent_update_hub.broadcast_threadsafe({
                "event": "SCENARIO_READY",
                "negotiation_id": data.get("negotiation_id"),
                "farmer": data.get("farmer"),
                "crop": data.get("crop"),
                "status": data.get("status")
            }, loop=loop)
             return

        if not message:
            return

        agent_update_hub.broadcast_threadsafe({
            "event": "NEGOTIATION_LOG",
            "negotiation_id": neg_id,
            "message": message,
            "agent_type": agent_type,
            "offer": offer,
        }, loop=loop)

    try:
        result = await loop.run_in_executor(
            _executor,
            lambda: negotiation_controller.start_negotiation(
                payload,
                scenario="direct-sale",
                pre_id=neg_id,
                live_event_callback=_broadcast_progress_event,
            ),
        )
    except Exception as exc:
        result = {
            "negotiation_id": neg_id,
            "status": "FAILED",
            "logs": [f"Error: {exc}"],
            "summary": "Negotiation failed due to an internal error.",
            "final_price": None,
            "offers": [],
            "market_offers": [],
            "selected_buyer": None,
        }
        await Database.update_negotiation_async(neg_id, result)
        negotiation_controller.service.active_negotiations[neg_id] = result

    for log_line in result.get("logs", []):
        await agent_update_hub.broadcast({
            "event": "NEGOTIATION_LOG",
            "negotiation_id": result.get("negotiation_id", neg_id),
            "message": log_line,
        })

    await agent_update_hub.broadcast({
        "event": "NEGOTIATION_FINISHED",
        "negotiation_id": result.get("negotiation_id", neg_id),
        "status": result.get("status"),
        "final_price": result.get("final_price"),
        "summary": result.get("summary"),
        "logs": result.get("logs", []),
        "market_offers": result.get("market_offers", []),
        "selected_buyer": result.get("selected_buyer"),
    })

@router.post("/start")
async def start_negotiation(
    request: StartNegotiationRequest, 
    background_tasks: BackgroundTasks, 
    current_user: dict = Depends(get_current_active_user)
):
    """
    Returns immediately with negotiation_id + status=RUNNING.
    The negotiation is submitted to Redis Streams for decoupling.
    """
    payload = request.model_dump()
    payload["user_id"] = current_user["sub"]
    neg_id = Database.generate_id("neg")

    running_entry = {
        "user_id": payload.get("user_id"),
        "negotiation_id": neg_id,
        "status": "RUNNING",
        "logs": ["🚀 Negotiation initiated. Processing..."],
        "summary": "Processing…",
        "final_price": None,
        "offers": [],
        "market_offers": [],
        "selected_buyer": None,
        "transport_plan": None,
    }
    await Database.create_negotiation_async(running_entry)
    negotiation_controller.service.active_negotiations[neg_id] = running_entry

    queued = False
    if redis_manager.client:
        try:
            await redis_manager.client.xadd(
                "agri:negotiation:jobs",
                {"payload": json.dumps(payload), "neg_id": neg_id}
            )
            logger.info(f"Successfully queued negotiation job {neg_id} in Redis Stream.")
            queued = True
        except Exception as e:
            logger.warning(f"Failed to queue in Redis Stream: {e}. Falling back to BackgroundTask.")

    if not queued:
        background_tasks.add_task(_run_negotiation_bg, payload, neg_id)

    await agent_update_hub.broadcast({
        "event": "NEGOTIATION_STARTED",
        "negotiation_id": neg_id,
        "status": "RUNNING",
    })

    return running_entry

@router.get("/{negotiation_id}/status")
async def get_negotiation_status(
    negotiation_id: str, 
    current_user: dict = Depends(get_current_active_user)
):
    return negotiation_controller.get_negotiation_status(negotiation_id)

@router.get("/")
async def list_negotiations(
    user_id: str = None, 
    role: str = None, 
    status: str = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Return negotiations filtered by role/user, most-recent first (max 50)."""
    negs = list(Database.negotiations.values())
    negs.reverse()
    recent = negs[:100]

    history_lookup: dict = {}
    for entry in await Database.get_history_async("all"):
        neg_id = entry.get("negotiation_id")
        if neg_id and neg_id not in history_lookup:
            history_lookup[neg_id] = entry

    enriched = []
    for neg in recent:
        neg_id = neg.get("negotiation_id", "")
        hist = history_lookup.get(neg_id, {})
        row = {
            **neg,
            "user_id":         neg.get("user_id")       or hist.get("user_id"),
            "farmer":          neg.get("farmer")         or hist.get("farmer"),
            "crop":            neg.get("crop")           or hist.get("crop"),
            "quantity":        neg.get("quantity")       or hist.get("quantity"),
            "final_price":     neg.get("final_price")    or hist.get("final_price"),
            "agents_involved": neg.get("agents_involved") or (
                [n for n in [hist.get("farmer"), hist.get("selected_buyer")] if n]
            ),
            "logs":            neg.get("logs", [])       or hist.get("logs", []),
        }
        enriched.append(row)

    if status:
        enriched = [n for n in enriched if str(n.get("status", "")).upper() == status.upper()]

    if role:
        role = role.lower()
        if role == "farmer" and user_id:
            enriched = [n for n in enriched if n.get("user_id") == user_id or n.get("farmer_id") == user_id]
        elif role == "buyer":
            if user_id:
                enriched = [n for n in enriched if n.get("user_id") == user_id or
                            str((n.get("selected_buyer") or {}).get("buyer_name", "")).lower() ==
                            str(n.get("buyer_name", "")).lower()]
            else:
                enriched = [n for n in enriched if n.get("selected_buyer")]
        elif role == "warehouse":
            enriched = [n for n in enriched if "STORAGE" in str(n.get("status", "")).upper()]
        elif role == "processor":
            enriched = [n for n in enriched if "PROCESSING" in str(n.get("status", "")).upper()]
        elif role == "compost":
            enriched = [n for n in enriched if "COMPOST" in str(n.get("status", "")).upper()]
        elif role == "transporter":
            enriched = [n for n in enriched if n.get("transport_plan") or
                        "transport" in str(n.get("next_action", "")).lower()]
        elif role == "restaurant":
            enriched = [n for n in enriched if "restaurant" in str(
                (n.get("selected_buyer") or {}).get("buyer_name", "")).lower() or
                       n.get("user_id") == user_id]
    elif user_id:
        enriched = [n for n in enriched if n.get("user_id") == user_id]

    return {"negotiations": enriched[:50]}

@router.post("/{negotiation_id}/approve")
async def approve_negotiation(
    negotiation_id: str, 
    role: str = "farmer",
    current_user: dict = Depends(get_current_active_user)
):
    """Role-based multi-signature handshake for multi-party consensus."""
    neg = await Database.get_negotiation_async(negotiation_id)
    if not neg:
         raise HTTPException(status_code=404, detail="Negotiation not found")
    
    if "signatures" not in neg:
        neg["signatures"] = {
            "farmer": False,
            "buyer": False,
            "transporter": False if neg.get("transport_plan") else True
        }
    
    neg["signatures"][role] = True
    
    all_signed = all(neg["signatures"].values())
    
    if all_signed:
        neg["status"] = "CONTRACT"
        neg["is_approved"] = True
        
        hub.record_signed_deal({
            "neg_id": negotiation_id,
            "buyer": neg.get("selected_buyer", {}).get("buyer_name", "Network Peer"),
            "farmer": neg.get("farmer") or neg.get("farmer_name"),
            "final_price": neg.get("final_price"),
            "logistics": neg.get("transport_plan", "Local Self-Pickup"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    else:
        neg["status"] = "PENDING_APPROVAL"

    await Database.update_negotiation_async(negotiation_id, neg)

    final_trust = None
    if all_signed:
        farmer_id = neg.get("user_id") or neg.get("farmer_id")
        if farmer_id:
            user = await UserRepository.get_by_id(farmer_id)
            if user:
                old_score = user.get("trust_score", 4.0)
                new_score = round(min(5.0, old_score + 0.1), 2)
                user["trust_score"] = new_score
                await UserRepository.upsert(user)
                final_trust = new_score
    
    msg = f"✍️ {role.capitalize()} node signed negotiation {negotiation_id[:8]}…"
    if all_signed:
        msg = "🤝 FULL CONSENSUS REACHED. Handshake committed to Ledger! ✅"
    
    await agent_update_hub.broadcast({
        "event": "NEGOTIATION_LOG",
        "negotiation_id": negotiation_id,
        "message": msg,
        "agent_type": "admin" if all_signed else role
    })
    
    if all_signed:
        await agent_update_hub.broadcast({
            "event": "CONTRACT_FINALIZED",
            "negotiation_id": negotiation_id,
            "farmer": neg.get("farmer") or neg.get("farmer_name"),
            "status": "CONTRACT",
            "trust_score": final_trust
        })
    
    return {
        "status": "success" if all_signed else "pending_others",
        "negotiation_id": negotiation_id,
        "signatures": neg["signatures"]
    }
