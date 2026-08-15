from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.v1.dependencies import get_db
from backend.services.simulation_service import run_simulation as run_simulation_service
from ..schemas.negotiation_model import SimulationRequest

router = APIRouter()

@router.post("/run-simulation")
async def run_simulation(
    request: SimulationRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await run_simulation_service(request.model_dump(), db=db)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/simulate")
async def simulate_alias(
    request: SimulationRequest,
    db: AsyncSession = Depends(get_db)
):
    return await run_simulation(request, db=db)

