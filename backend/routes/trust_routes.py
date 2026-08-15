"""
backend/routes/trust_routes.py

Trust Engine API — view and update trust scores.
"""

from backend.repositories.user_repository import UserRepository
from fastapi import APIRouter, Depends, HTTPException
from backend.services.security import get_current_user
from database.db import Database

router = APIRouter(tags=["Trust"])


@router.get("/score/{user_id}")
async def get_trust_score(user_id: str, current_user: dict = Depends(get_current_user)):
    """Return current trust score for any user."""
    user = await UserRepository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "success": True,
        "data": {
            "user_id": user_id,
            "name": user.get("name"),
            "role": user.get("role"),
            "trust_score": user.get("trust_score", 4.0),
            "verification_status": user.get("verification_status", "PENDING"),
        },
    }


@router.post("/update/{user_id}")
async def update_trust_score(
    user_id: str,
    event: str,  # "deal_completed" | "default" | "late_delivery"
    current_user: dict = Depends(get_current_user),
):
    """Apply a trust event and recalculate score."""
    user = await UserRepository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_score = float(user.get("trust_score", 4.0))

    DELTA_MAP = {
        "deal_completed": 0.1,
        "verified_document": 0.2,
        "late_delivery": -0.5,
        "default": -1.5,
        "cancellation": -0.8,
    }

    delta = DELTA_MAP.get(event, 0.0)
    new_score = round(max(0.0, min(5.0, old_score + delta)), 2)

    user["trust_score"] = new_score
    await UserRepository.upsert(user)

    return {
        "success": True,
        "data": {
            "user_id": user_id,
            "event": event,
            "old_score": old_score,
            "delta": delta,
            "new_score": new_score,
        },
    }

@router.post("/record-outcome")
async def record_outcome(
    user_id: str,
    event: str,
    current_user: dict = Depends(get_current_user)
):
    return await update_trust_score(user_id, event, current_user)


@router.get("/my-score")
async def my_trust_score(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user's own trust score."""
    uid = current_user["sub"]
    user = await UserRepository.get_by_id(uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "success": True,
        "data": {
            "trust_score": user.get("trust_score", 4.0),
            "verification_status": user.get("verification_status", "PENDING"),
        },
    }

