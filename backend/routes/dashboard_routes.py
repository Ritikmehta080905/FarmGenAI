"""
backend/routes/dashboard_routes.py

Dashboard API endpoints — FR-13: Analytics & Dashboard
Serves data for farmer dashboard, buyer dashboard, and admin overview.
"""

from backend.repositories.user_repository import UserRepository
from fastapi import APIRouter, Depends
from backend.services.security import get_current_user
from backend.services.dashboard_service import (
    get_platform_summary, get_farmer_dashboard, get_buyer_dashboard
)

router = APIRouter(tags=["Dashboard"])


@router.get("/platform")
async def platform_dashboard(current_user: dict = Depends(get_current_user)):
    """
    Platform-wide aggregated stats (admin view).
    Includes negotiation outcomes, price analytics, GMV, crop distribution.
    """
    data = await get_platform_summary()
    return {"success": True, "data": data}


@router.get("/farmer")
async def farmer_dashboard(current_user: dict = Depends(get_current_user)):
    """Dashboard statistics for the authenticated farmer."""
    uid = current_user["sub"]
    data = await get_farmer_dashboard(uid)
    return {"success": True, "data": data}


@router.get("/buyer")
async def buyer_dashboard(current_user: dict = Depends(get_current_user)):
    """Dashboard statistics for the authenticated buyer."""
    uid = current_user["sub"]
    data = await get_buyer_dashboard(uid)
    return {"success": True, "data": data}


@router.get("/user/{user_id}")
async def user_dashboard(user_id: str, current_user: dict = Depends(get_current_user)):
    """
    Dashboard for a specific user — role-aware response.
    Farmers get farmer stats, buyers get buyer stats.
    """
    from database.db import Database
    user = await UserRepository.get_by_id(user_id) or {}
    role = user.get("role", "farmer")

    if role == "buyer":
        data = await get_buyer_dashboard(user_id)
    else:
        data = await get_farmer_dashboard(user_id)

    return {"success": True, "role": role, "data": data}
