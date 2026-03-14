from database.db import Database


def add_history(user_id: str, item: dict):
    if not user_id:
        return

    if user_id not in Database.history:
        Database.history[user_id] = []

    Database.history[user_id].append(item)


def get_user_history(user_id: str):
    return {
        "user_id": user_id,
        "history": Database.history.get(user_id, [])
    }