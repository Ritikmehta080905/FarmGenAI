from fastapi import APIRouter, Depends, HTTPException
from ..controllers.negotiation_controller import NegotiationController
from ..models.negotiation_model import StartNegotiationRequest
from backend.services.security import get_current_user

router = APIRouter()
controller = NegotiationController()

@router.post("/start-negotiation")
async def start_negotiation(
    request: StartNegotiationRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        payload = request.model_dump()
        if current_user and current_user.get("sub"):
            payload["user_id"] = current_user["sub"]
        return await controller.start_negotiation(payload, scenario="direct-sale")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/negotiation-status/{negotiation_id}")
async def get_negotiation_status(negotiation_id: str):
    try:
        status = await controller.get_negotiation_status(negotiation_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/agents")
async def get_agents():
    try:
        return {"agents": await controller.get_agents()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
