from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .routes.buyer_routes import router as buyer_router
from .routes.farmer_routes import router as farmer_router
from .routes.negotiation_routes import router as negotiation_router
from .routes.simulation_routes import router as simulation_router
from .routes.warehouse_routes import router as warehouse_router
from .controllers.negotiation_controller import NegotiationController
from .controllers.simulation_controller import run_simulation_controller
from .models.negotiation_model import StartNegotiationRequest, SimulationRequest
from .websocket.agent_updates import agent_update_hub

app = FastAPI(title="AgriNegotiator API", version="1.0.0")
negotiation_controller = NegotiationController()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(buyer_router, prefix="/api/buyer", tags=["Buyer"])
app.include_router(farmer_router, prefix="/api/farmer", tags=["Farmer"])
app.include_router(negotiation_router, prefix="/api/negotiation", tags=["Negotiation"])
app.include_router(simulation_router, prefix="/api/simulation", tags=["Simulation"])
app.include_router(warehouse_router, prefix="/api/warehouse", tags=["Warehouse"])

@app.get("/")
async def root():
    return {"message": "Welcome to AgriNegotiator API"}


@app.post("/start-negotiation")
async def start_negotiation(request: StartNegotiationRequest):
    result = negotiation_controller.start_negotiation(request.model_dump(), scenario="direct-sale")
    await agent_update_hub.broadcast(
        {
            "event": "NEGOTIATION_STARTED",
            "negotiation_id": result["negotiation_id"],
            "status": result["status"],
            "logs": result.get("logs", [])
        }
    )
    for log in result.get("logs", []):
        await agent_update_hub.broadcast(
            {
                "event": "NEGOTIATION_LOG",
                "negotiation_id": result["negotiation_id"],
                "message": log
            }
        )

    await agent_update_hub.broadcast(
        {
            "event": "NEGOTIATION_FINISHED",
            "negotiation_id": result["negotiation_id"],
            "status": result["status"],
            "final_price": result.get("final_price"),
            "summary": result.get("summary")
        }
    )
    return result


@app.get("/negotiation-status/{negotiation_id}")
async def negotiation_status(negotiation_id: str):
    return negotiation_controller.get_negotiation_status(negotiation_id)


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
