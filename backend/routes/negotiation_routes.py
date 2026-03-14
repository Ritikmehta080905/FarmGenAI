from fastapi import APIRouter, HTTPException
from ..controllers.negotiation_controller import NegotiationController
from ..models.negotiation_model import StartNegotiationRequest

router = APIRouter()
controller = NegotiationController()

@router.post("/start-negotiation")
async def start_negotiation(request: StartNegotiationRequest):
    try:
        return controller.start_negotiation(request.model_dump(), scenario="direct-sale")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/negotiation-status/{negotiation_id}")
async def get_negotiation_status(negotiation_id: str):
    try:
        status = controller.get_negotiation_status(negotiation_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/agents")
async def get_agents():
    try:
        return {"agents": controller.get_agents()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
