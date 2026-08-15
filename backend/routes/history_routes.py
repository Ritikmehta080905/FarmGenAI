from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.v1.dependencies import get_db
from backend.services.history_service import get_user_history
from backend.schemas.history_model import HistoryResponse
from backend.core.security import get_current_user

router = APIRouter(tags=["History"])


@router.get("/history/{user_id}", response_model=HistoryResponse)
async def history(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    auth_user_id = current_user["sub"]
    role = current_user.get("role")
    # Enforce history boundaries
    if auth_user_id != user_id and role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: You cannot access history for other users.")
    return await get_user_history(user_id, db=db)
