from database.db import Database


async def add_history(user_id: str, item: dict, db=None):
    if not user_id:
        return
    await Database(db).add_history_async(user_id, item)


async def get_user_history(user_id: str, db=None):
    return {
        "user_id": user_id,
        "history": await Database(db).get_history_async(user_id),
    }

