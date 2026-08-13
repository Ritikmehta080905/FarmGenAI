from fastapi import APIRouter, Depends
from ..controllers.buyer_controller import create_buyer_offer_controller, get_buyer_offers_controller, get_buyers_controller
from ..models.buyer_model import BuyerOfferCreate
from backend.services.security import get_current_user, require_role

router = APIRouter()

@router.get("/")
async def get_buyers(current_user: dict = Depends(get_current_user)):
    return {"buyers": get_buyers_controller()}


@router.get("/offers")
async def get_buyer_offers(user_id: str | None = None, current_user: dict = Depends(require_role("buyer"))):
    return {"offers": get_buyer_offers_controller(user_id=user_id)}


@router.post("/offers")
async def create_buyer_offer(payload: BuyerOfferCreate, current_user: dict = Depends(require_role("buyer"))):
    data = payload.model_dump()
    # Enforce authenticated user ID
    data["user_id"] = current_user["sub"]
    return create_buyer_offer_controller(data)
