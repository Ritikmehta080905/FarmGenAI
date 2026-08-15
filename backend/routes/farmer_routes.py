from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.v1.dependencies import get_db
from backend.core.security import require_role
from backend.services.negotiation_service import list_farmers, list_produce

router = APIRouter()

@router.get("/")
async def get_farmers(
    current_user: dict = Depends(require_role("farmer", "admin", "buyer")),
    db: AsyncSession = Depends(get_db)
):
    return {"farmers": await list_farmers(db=db)}


@router.get("/produce")
async def get_produce(
    current_user: dict = Depends(require_role("farmer", "admin", "buyer")),
    db: AsyncSession = Depends(get_db)
):
    return {"produce": await list_produce(db=db)}


