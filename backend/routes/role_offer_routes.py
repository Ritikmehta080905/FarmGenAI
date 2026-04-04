from fastapi import APIRouter, HTTPException

from ..models.role_offer_model import RoleOfferCreate
from ..services.role_offer_service import create_role_offer, list_role_offers

router = APIRouter()


@router.get("/")
async def get_role_offers(role: str | None = None, user_id: str | None = None):
    return {"offers": list_role_offers(role=role, user_id=user_id)}


@router.post("/")
async def post_role_offer(payload: RoleOfferCreate):
    try:
        return create_role_offer(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
