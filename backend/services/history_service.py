from database.db import Database


def add_history(user_id: str, item: dict):
    if not user_id:
        return
    Database.add_history(user_id, item)


def get_user_history(user_id: str):
    return {
        "user_id": user_id,
        "history": Database.get_history(user_id),
    }
