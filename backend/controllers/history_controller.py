from backend.services.history_service import get_user_history


def get_history_controller(user_id: str):
    return get_user_history(user_id)