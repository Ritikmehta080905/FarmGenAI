from fastapi import APIRouter
from backend.controllers.simulation_controller import run_simulation_controller
from backend.models.negotiation_model import SimulationRequest, NegotiationResponse

router = APIRouter(tags=["Simulation"])


@router.post("/run-simulation", response_model=NegotiationResponse)
def simulation(payload: SimulationRequest):
    return run_simulation_controller(payload.dict())