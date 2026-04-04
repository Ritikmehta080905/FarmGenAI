from fastapi import APIRouter
from ..controllers.buyer_controller import create_buyer_offer_controller, get_buyer_offers_controller, get_buyers_controller
from ..models.buyer_model import BuyerOfferCreate

router = APIRouter()

@router.get("/")
async def get_buyers():
    return {"buyers": get_buyers_controller()}


@router.get("/offers")
async def get_buyer_offers(user_id: str | None = None):
    return {"offers": get_buyer_offers_controller(user_id=user_id)}


@router.post("/offers")
async def create_buyer_offer(payload: BuyerOfferCreate):
    return create_buyer_offer_controller(payload.model_dump())
