from fastapi import APIRouter, HTTPException
from ..controllers.simulation_controller import run_simulation_controller
from ..models.negotiation_model import SimulationRequest

router = APIRouter()

@router.post("/run-simulation")
async def run_simulation(request: SimulationRequest):
    try:
        return run_simulation_controller(request.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
