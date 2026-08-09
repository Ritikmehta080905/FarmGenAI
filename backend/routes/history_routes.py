from fastapi import APIRouter, Depends, HTTPException
from backend.controllers.history_controller import get_history_controller
from backend.models.history_model import HistoryResponse
from backend.services.security import get_current_user

router = APIRouter(tags=["History"])


@router.get("/history/{user_id}", response_model=HistoryResponse)
async def history(user_id: str, current_user: dict = Depends(get_current_user)):
    auth_user_id = current_user["sub"]
    role = current_user.get("role")
    # Enforce history boundaries
    if auth_user_id != user_id and role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: You cannot access history for other users.")
    return get_history_controller(user_id)