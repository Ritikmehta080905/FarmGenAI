from typing import AsyncGenerator
from backend.db.session import AsyncSessionLocal

async def get_db() -> AsyncGenerator:
    """
    Dependency to yield an async database session for the duration of the request.
    This ensures proper transaction scoping and rollback on exceptions.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

