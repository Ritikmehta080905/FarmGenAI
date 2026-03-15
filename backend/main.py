import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import BackgroundTasks, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .routes.buyer_routes import router as buyer_router
from .routes.farmer_routes import router as farmer_router
from .routes.history_routes import router as history_router
from .routes.negotiation_routes import router as negotiation_router
from .routes.simulation_routes import router as simulation_router
from .routes.warehouse_routes import router as warehouse_router
from .routes.auth_routes import router as auth_router
from .controllers.negotiation_controller import NegotiationController
from .controllers.simulation_controller import run_simulation_controller
from .models.negotiation_model import StartNegotiationRequest, SimulationRequest
from .websocket.agent_updates import agent_update_hub
from database.db import Database

app = FastAPI(title="AgriNegotiator API", version="1.0.0")
negotiation_controller = NegotiationController()
_executor = ThreadPoolExecutor(max_workers=4)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(buyer_router, prefix="/api/buyer", tags=["Buyer"])
app.include_router(farmer_router, prefix="/api/farmer", tags=["Farmer"])
app.include_router(history_router, prefix="/api", tags=["History"])
app.include_router(negotiation_router, prefix="/api/negotiation", tags=["Negotiation"])
app.include_router(simulation_router, prefix="/api/simulation", tags=["Simulation"])
app.include_router(warehouse_router, prefix="/api/warehouse", tags=["Warehouse"])

@app.get("/")
async def root():
    return {"message": "Welcome to AgriNegotiator API"}


# ── Background negotiation helper ────────────────────────────────

async def _run_negotiation_bg(payload: dict, neg_id: str):
    """Run the blocking negotiation in a thread-pool, then push WS events."""
    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(
            _executor,
            lambda: negotiation_controller.start_negotiation(payload, scenario="direct-sale", pre_id=neg_id),
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
async def start_negotiation(request: StartNegotiationRequest, background_tasks: BackgroundTasks):
    """
    Returns immediately with negotiation_id + status=RUNNING.
    The actual negotiation (possibly involving slow LLM calls) is executed in a
    background thread so the HTTP request never times out.
    Poll /negotiation-status/{id} or listen on /ws/negotiation for results.
    """
    payload = request.model_dump()
    neg_id = Database.generate_id("neg")

    # Seed a placeholder so the status endpoint returns something right away
    running_entry = {
        "negotiation_id": neg_id,
        "status": "RUNNING",
        "logs": ["🚀 Negotiation started. LLM agents are reasoning…"],
        "summary": "Processing…",
        "final_price": None,
        "offers": [],
        "market_offers": [],
        "selected_buyer": None,
        "transport_plan": None,
    }
    Database.create_negotiation(running_entry)
    negotiation_controller.service.active_negotiations[neg_id] = running_entry

    background_tasks.add_task(_run_negotiation_bg, payload, neg_id)

    await agent_update_hub.broadcast({
        "event": "NEGOTIATION_STARTED",
        "negotiation_id": neg_id,
        "status": "RUNNING",
    })

    return running_entry


@app.get("/negotiation-status/{negotiation_id}")
async def negotiation_status(negotiation_id: str):
    return negotiation_controller.get_negotiation_status(negotiation_id)


@app.get("/api/negotiations")
async def list_negotiations():
    """Return all negotiations, most-recent first (max 50), enriched with history data."""
    negs = list(Database.negotiations.values())
    negs.reverse()
    recent = negs[:50]

    # Build a lookup from history so older records (pre-fix) can still show
    # farmer name, crop, final_price that were not saved in the raw negotiation row.
    history_lookup: dict = {}
    for entry in Database.get_history("all"):
        neg_id = entry.get("negotiation_id")
        if neg_id and neg_id not in history_lookup:
            history_lookup[neg_id] = entry

    enriched = []
    for neg in recent:
        neg_id = neg.get("negotiation_id", "")
        hist = history_lookup.get(neg_id, {})
        enriched.append({
            **neg,
            # Fill in missing fields from history so old records display too
            "farmer":          neg.get("farmer")      or hist.get("farmer"),
            "crop":            neg.get("crop")         or hist.get("crop"),
            "quantity":        neg.get("quantity")     or hist.get("quantity"),
            "final_price":     neg.get("final_price")  or hist.get("final_price"),
            "agents_involved": neg.get("agents_involved") or (
                [n for n in [hist.get("farmer"), hist.get("selected_buyer")] if n]
            ),
            "logs":            neg.get("logs", [])    or hist.get("logs", []),
        })

    return {"negotiations": enriched}


@app.get("/agents")
async def agents():
    return {"agents": negotiation_controller.get_agents()}


@app.post("/run-simulation")
async def run_simulation(request: SimulationRequest):
    result = run_simulation_controller(request.model_dump())
    await agent_update_hub.broadcast(
        {
            "event": "SIMULATION_FINISHED",
            "result": result,
        }
    )
    return result


@app.websocket("/ws/negotiation")
async def negotiation_updates(websocket: WebSocket):
    await agent_update_hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        agent_update_hub.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
