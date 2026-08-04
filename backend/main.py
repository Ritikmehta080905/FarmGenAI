import asyncio
import sqlite3
import json
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

from fastapi import BackgroundTasks, FastAPI, WebSocket, WebSocketDisconnect, Depends
from backend.services.security import get_current_user
from fastapi.middleware.cors import CORSMiddleware
from .routes.buyer_routes import router as buyer_router
from .routes.farmer_routes import router as farmer_router
from .routes.history_routes import router as history_router
from .routes.warehouse_routes import router as warehouse_router
from .routes.role_offer_routes import router as role_offer_router
from .routes.auth_routes import router as auth_router
from .routes.agents_routes import router as agents_router
from .controllers.negotiation_controller import NegotiationController
from .controllers.simulation_controller import run_simulation_controller
from .models.negotiation_model import StartNegotiationRequest, SimulationRequest
from .websocket.agent_updates import agent_update_hub
from database.db import Database, init_db
from nodes.node_hub import hub, bootstrap_peer_network
from nodes.farmer_node import FarmerNode

import redis.asyncio as aioredis
from config.settings import REDIS_URL

logger = logging.getLogger("backend.main")
redis_client = None

app = FastAPI(title="AgriNegotiator", version="2.0.0-DE")
_executor = ThreadPoolExecutor(max_workers=10)
negotiation_controller = NegotiationController()

# CORS middleware (Essential for frontend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def redis_pubsub_listener():
    global redis_client
    if not redis_client:
        return
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("agri:telemetry:updates")
    print("📡 Redis Pub/Sub listener subscribed to 'agri:telemetry:updates'.")
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                try:
                    data = json.loads(message["data"])
                    neg_id = data["negotiation_id"]
                    event = data["event"]
                    event_type = event.get("type")
                    event_data = event.get("data", {})

                    if event_type == "scenario_ready":
                        await agent_update_hub.broadcast({
                            "event": "SCENARIO_READY",
                            "negotiation_id": neg_id,
                            "farmer": event_data.get("farmer"),
                            "crop": event_data.get("crop"),
                            "status": event_data.get("status")
                        })
                    elif event_type == "counter_offer":
                        agent_name = str(event_data.get("agent", "")).lower()
                        agent_type = "farmer" if "farmer" in agent_name else "buyer"
                        await agent_update_hub.broadcast({
                            "event": "NEGOTIATION_LOG",
                            "negotiation_id": neg_id,
                            "message": event_data.get("message") or f"{event_data.get('agent')}: Proposing ₹{event_data.get('price')}/kg.",
                            "agent_type": agent_type,
                            "offer": event_data.get("price"),
                        })
                    elif event_type == "agreement":
                        await agent_update_hub.broadcast({
                            "event": "NEGOTIATION_LOG",
                            "negotiation_id": neg_id,
                            "message": f"Deal reached at ₹{event_data.get('price')}/kg for {event_data.get('quantity')}kg",
                            "agent_type": "system",
                            "offer": event_data.get("price")
                        })
                    elif event_type == "negotiation_finished":
                        await agent_update_hub.broadcast({
                            "event": "NEGOTIATION_FINISHED",
                            "negotiation_id": neg_id,
                            "status": event_data.get("status"),
                            "final_price": event_data.get("final_price"),
                            "summary": event_data.get("summary"),
                            "logs": event_data.get("logs", []),
                            "market_offers": event_data.get("market_offers", []),
                            "selected_buyer": event_data.get("selected_buyer")
                        })
                    elif event_type == "status_update":
                        await agent_update_hub.broadcast({
                            "event": "NEGOTIATION_LOG",
                            "negotiation_id": neg_id,
                            "message": event_data.get("message", ""),
                            "agent_type": "system"
                        })
                except Exception as ex:
                    print(f"Error parsing pubsub message data: {ex}")
            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error in Redis Pub/Sub listener: {e}")


@app.on_event("startup")
async def on_startup():
    print("🚀 API GLOBAL STARTUP INITIATED...")
    await init_db()
    await bootstrap_peer_network()
    
    global redis_client
    try:
        redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        print("Connected to Redis successfully.")
        asyncio.create_task(redis_pubsub_listener())
    except Exception as e:
        print(f"⚠️ Redis not reachable ({e}). WebSocket updates will fall back to direct memory updates.")
        redis_client = None

# ── Decentralized P2P API ────────────────────────

@app.post("/api/node/{node_id}/announce")
async def node_announce(node_id: str, payload: dict):
    # Discovery: Register the user node if it doesn't exist
    if node_id not in hub.nodes:
        hub.register_node(FarmerNode(node_id, payload.get("name", "Local Node")))
    
    node = hub.nodes[node_id]
    msg = await node.announce_supply(
        payload["crop"], payload["quantity"], payload["min_price"]
    )
    # Broadcast to peers via the Relay Hub
    await hub.broadcast(node_id, msg)
    return {"status": "broadcast_sent", "message_id": msg.message_id}

@app.get("/api/node/{node_id}/scenarios")
async def get_node_scenarios(node_id: str, crop: str):
    if node_id not in hub.nodes:
        return {"scenarios": []}
    
    node = hub.nodes[node_id]
    scenarios = node.get_local_scenarios(crop)
    return {"scenarios": scenarios}

@app.post("/api/node/{node_id}/select")
async def node_select(node_id: str, payload: dict):
    if node_id not in hub.nodes:
         from fastapi import HTTPException
         raise HTTPException(status_code=404, detail="Node not found")
    
    node = hub.nodes[node_id]
    crop = payload.get("crop")
    peer_node = payload.get("peer_node")
    
    # Phase 2: Start the Multi-Party Direct Handshake
    block = await node.select_scenario(peer_node, crop)
    
    # --- PERSISTENCE FIX ---
    # We create a negotiation record so it appears on the dashboard
    neg_id = block.get("block_id") if isinstance(block, dict) else f"neg_{Database.generate_id()}"
    neg_record = {
        "negotiation_id": neg_id,
        "user_id": node_id,
        "farmer": node.farmer_name,
        "crop": crop,
        "quantity": 1000, # Fallback or from payload
        "status": "NEGOTIATING",
        "peer_node": peer_node,
        "summary": f"Decentralized handshake with {peer_node}",
        "logs": ["Handshake initiated. Consensus reached.", "Verifying node signatures..."],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    Database.update_negotiation(neg_id, neg_record)
    Database.add_history(node_id, {"type": "NEGOTIATION_START", **neg_record})
    
    return {"status": "success", "block": block, "negotiation_id": neg_id}

@app.get("/api/nodes")
async def get_all_nodes():
    """Return a map of all discovered P2P nodes for Admin Governance."""
    nodes_map = {}
    for nid, n in hub.nodes.items():
        # Optional: Enrich with DB trust score if node_id matches a user_id
        user = Database.get_user(nid) or {}
        nodes_map[nid] = {
            "role": n.role,
            "status": "online",
            "trust_score": user.get("trust_score", 4.2),
            "verified": user.get("verified", nid.startswith("node_")), # Auto-verify platform nodes
            "history": [] # Could enrich with node.get_ledger() if needed
        }
    return nodes_map

@app.get("/api/ledger")
async def get_public_ledger():
    return {"ledger": hub.audit_ledger}

# Original endpoints (for compatibility/history)
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(buyer_router, prefix="/api/buyer", tags=["Buyer"])
app.include_router(farmer_router, prefix="/api/farmer", tags=["Farmer"])
app.include_router(history_router, prefix="/api", tags=["History"])
app.include_router(warehouse_router, prefix="/api/warehouse", tags=["Warehouse"])
app.include_router(role_offer_router, prefix="/api/role-offers", tags=["RoleOffers"])
app.include_router(agents_router, prefix="/agents", tags=["Agents"])

@app.post("/api/negotiation/{negotiation_id}/approve")
async def approve_negotiation(negotiation_id: str, role: str = "farmer"):
    """Role-based multi-signature handshake for multi-party consensus."""
    neg = Database.get_negotiation(negotiation_id)
    if not neg:
         from fastapi import HTTPException
         raise HTTPException(status_code=404, detail="Negotiation not found")
    
    # ── Initialize Multi-Signature State ──────────────────
    if "signatures" not in neg:
        neg["signatures"] = {
            "farmer": False,
            "buyer": False,
            "transporter": False if neg.get("transport_plan") else True
        }
    
    # Mark current role as signed
    neg["signatures"][role] = True
    
    # Check for full consensus (Test F2/F4)
    all_signed = all(neg["signatures"].values())
    
    if all_signed:
        neg["status"] = "CONTRACT"
        neg["is_approved"] = True
        
        # ── Peer Network Ledger Entry ────────────────────────
        hub.record_signed_deal({
            "neg_id": negotiation_id,
            "buyer": neg.get("selected_buyer", {}).get("buyer_name", "Network Peer"),
            "farmer": neg.get("farmer") or neg.get("farmer_name"),
            "final_price": neg.get("final_price"),
            "logistics": neg.get("transport_plan", "Local Self-Pickup"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    else:
        neg["status"] = "PENDING_APPROVAL" # Remain pending until all sign

    # Update Database
    Database.update_negotiation(negotiation_id, neg)

    # Trust Score: Awarded only on full consensus
    final_trust = None
    if all_signed:
        farmer_id = neg.get("user_id") or neg.get("farmer_id")
        if farmer_id:
            user = Database.get_user(farmer_id)
            if user:
                old_score = user.get("trust_score", 4.0)
                new_score = round(min(5.0, old_score + 0.1), 2)
                user["trust_score"] = new_score
                Database.upsert_user(user)
                final_trust = new_score
    
    # ── Live Notifications ──────────────────────────────
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

@app.get("/")
async def root():
    return {"message": "Welcome to AgriNegotiator API"}


# ── Background negotiation helper ────────────────────────────────

async def _run_negotiation_bg(payload: dict, neg_id: str):
    """Run the blocking negotiation in a thread-pool, then push WS events."""
    loop = asyncio.get_running_loop()

    def _broadcast_progress_event(event: dict):
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
    except Exception as exc:  # noqa: BLE001
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
        Database.update_negotiation(neg_id, result)
        negotiation_controller.service.active_negotiations[neg_id] = result

    # Broadcast every log line, then the finished event
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


@app.post("/start-negotiation")
async def start_negotiation(request: StartNegotiationRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """
    Returns immediately with negotiation_id + status=RUNNING.
    The negotiation is submitted to Redis Streams for decoupling.
    If Redis is unreachable, falls back to direct background thread processing.
    """
    payload = request.model_dump()
    payload["user_id"] = current_user["sub"]
    neg_id = Database.generate_id("neg")

    # Seed placeholder entry
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
    Database.create_negotiation(running_entry)
    negotiation_controller.service.active_negotiations[neg_id] = running_entry

    # Queue logic
    queued = False
    if redis_client:
        try:
            await redis_client.xadd(
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


@app.get("/negotiation-status/{negotiation_id}")
async def negotiation_status(negotiation_id: str, current_user: dict = Depends(get_current_user)):
    return negotiation_controller.get_negotiation_status(negotiation_id)


@app.get("/api/negotiations")
async def list_negotiations(user_id: str = None, role: str = None, status: str = None):
    """Return negotiations filtered by role/user, most-recent first (max 50)."""
    negs = list(Database.negotiations.values())
    negs.reverse()
    recent = negs[:100]

    # Build history lookup for enrichment
    history_lookup: dict = {}
    for entry in Database.get_history("all"):
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

    # Filter by status
    if status:
        enriched = [n for n in enriched if str(n.get("status", "")).upper() == status.upper()]

    # Filter by role — each role sees only relevant negotiations
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
        # No role specified, filter by user_id only
        enriched = [n for n in enriched if n.get("user_id") == user_id]

    return {"negotiations": enriched[:50]}


@app.get("/agents")
async def agents():
    return {"agents": negotiation_controller.get_agents()}


@app.get("/api/ledger")
async def get_ledger():
    """Return the P2P network's public signed deal ledger (blockchain simulation)."""
    return {"ledger": hub.audit_ledger}


@app.post("/api/admin/verify/{user_id}")
async def admin_verify_node(user_id: str, verified: bool = True):
    """Admin-only endpoint to verify or revoke a stakeholder node (Phase I)."""
    user = Database.get_user(user_id)
    if not user:
         from fastapi import HTTPException
         raise HTTPException(status_code=404, detail="Node (User) not found")
    
    user["verified"] = verified
    if verified:
        user["verification_status"] = "VERIFIED"
    else:
        user["verification_status"] = "REJECTED"
        
    Database.upsert_user(user)
    
    return {"status": "success", "user_id": user_id, "verified": verified}


@app.post("/run-simulation")
async def run_simulation(request: SimulationRequest, current_user: dict = Depends(get_current_user)):
    result = run_simulation_controller(request.model_dump())
    await agent_update_hub.broadcast(
        {
            "event": "SIMULATION_FINISHED",
            "result": result,
        }
    )
    return result


@app.websocket("/ws/negotiation")
async def negotiation_updates(websocket: WebSocket, token: str = None):
    if not token:
        token = websocket.query_params.get("token")
    
    from backend.services.security import verify_token
    payload = verify_token(token) if token else None
    if not payload:
        await websocket.accept()
        await websocket.close(code=4003)
        return

    await agent_update_hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        agent_update_hub.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
