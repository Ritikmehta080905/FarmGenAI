from database.db import Database


async def add_history(user_id: str, item: dict):
    if not user_id:
        return
    await Database.add_history_async(user_id, item)


async def get_user_history(user_id: str):
    return {
        "user_id": user_id,
        "history": await Database.get_history_async(user_id),
    }
