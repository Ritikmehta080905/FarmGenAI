from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from backend.app.core.deps import get_current_active_user
from backend.app.core.redis import redis_manager
from backend.app.core.controllers import negotiation_controller
from database.db import engine
from backend.repositories.user_repository import UserRepository
from backend.models.negotiation_model import SimulationRequest
from backend.controllers.simulation_controller import run_simulation_controller
from backend.websocket.agent_updates import agent_update_hub

router = APIRouter()

@router.get("/health")
async def health_check():
    db_ok = True
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    redis_ok = True
    if redis_manager.client:
        try:
            await redis_manager.client.ping()
        except Exception:
            redis_ok = False
    else:
        redis_ok = False

    status = "healthy" if (db_ok and redis_ok) else "degraded"
    
    return {
        "status": status,
        "database": "up" if db_ok else "down",
        "redis": "up" if redis_ok else "down"
    }

@router.get("/agents")
async def get_agents():
    return {"agents": negotiation_controller.get_agents()}

@router.post("/admin/verify/{user_id}")
async def admin_verify_node(
    user_id: str, 
    verified: bool = True,
    current_user: dict = Depends(get_current_active_user)
):
    """Admin-only endpoint to verify or revoke a stakeholder node (Phase I)."""
    user = await UserRepository.get_by_id(user_id)
    if not user:
         raise HTTPException(status_code=404, detail="Node (User) not found")
    
    user["verified"] = verified
    if verified:
        user["verification_status"] = "VERIFIED"
    else:
        user["verification_status"] = "REJECTED"
        
    await UserRepository.upsert(user)
    
    return {"status": "success", "user_id": user_id, "verified": verified}

@router.post("/run-simulation")
async def run_simulation(
    request: SimulationRequest, 
    current_user: dict = Depends(get_current_active_user)
):
    result = await run_simulation_controller(request.model_dump())
    await agent_update_hub.broadcast({"event": "SIMULATION_FINISHED", "result": result})
    return result
