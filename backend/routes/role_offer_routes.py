from fastapi import APIRouter, HTTPException, Depends
from ..models.role_offer_model import RoleOfferCreate
from ..services.role_offer_service import create_role_offer, list_role_offers
from backend.services.security import get_current_user

router = APIRouter()


@router.get("/")
async def get_role_offers(role: str | None = None, user_id: str | None = None, current_user: dict = Depends(get_current_user)):
    return {"offers": await list_role_offers(role=role, user_id=user_id)}


@router.post("/")
async def post_role_offer(payload: RoleOfferCreate, current_user: dict = Depends(get_current_user)):
    try:
        data = payload.model_dump()
        # Enforce user_id matching sub parameter
        data["user_id"] = current_user["sub"]
        return await create_role_offer(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
