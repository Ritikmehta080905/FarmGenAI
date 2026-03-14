from fastapi import APIRouter, HTTPException
from ..controllers.negotiation_controller import NegotiationController

router = APIRouter()
controller = NegotiationController()

@router.post("/start")
async def start_negotiation(farmer_id: int, buyer_id: int):
    try:
        negotiation_id = controller.start_negotiation(farmer_id, buyer_id)
        return {"negotiation_id": negotiation_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{negotiation_id}/offer")
async def make_offer(negotiation_id: int, offer: dict):
    try:
        response = controller.make_offer(negotiation_id, offer)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{negotiation_id}/status")
async def get_negotiation_status(negotiation_id: int):
    try:
        status = controller.get_negotiation_status(negotiation_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail="Negotiation not found")
