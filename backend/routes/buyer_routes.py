from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.v1.dependencies import get_db
from backend.services.negotiation_service import create_buyer_offer, list_buyer_offers, list_buyers
from ..schemas.buyer_model import BuyerOfferCreate
from backend.core.security import get_current_user, require_role

router = APIRouter()

@router.get("/")
async def get_buyers(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return {"buyers": await list_buyers(db=db)}


@router.get("/offers")
async def get_buyer_offers(
    user_id: str | None = None,
    current_user: dict = Depends(require_role("buyer", "admin")),
    db: AsyncSession = Depends(get_db)
):
    return {"offers": await list_buyer_offers(user_id=user_id, db=db)}


@router.post("/offers")
async def add_buyer_offer(
    payload: BuyerOfferCreate,
    current_user: dict = Depends(require_role("buyer", "admin")),
    db: AsyncSession = Depends(get_db)
):
    data = payload.model_dump()
    data["user_id"] = current_user["sub"]
    return await create_buyer_offer(data, db=db)

