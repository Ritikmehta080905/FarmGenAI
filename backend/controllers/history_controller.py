from backend.services.history_service import get_user_history


async def get_history_controller(user_id: str):
    return await get_user_history(user_id)