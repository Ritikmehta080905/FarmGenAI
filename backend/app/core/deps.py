from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import AsyncSessionLocal
from backend.services.security import get_current_user

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting an async database session."""
    async with AsyncSessionLocal() as session:
        yield session

# Re-exporting for convenience
def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """Dependency for getting the current authenticated user."""
    return current_user
