from fastapi import APIRouter
from backend.controllers.history_controller import get_history_controller
from backend.models.history_model import HistoryResponse

router = APIRouter(tags=["History"])


@router.get("/history/{user_id}", response_model=HistoryResponse)
def history(user_id: str):
    return get_history_controller(user_id)