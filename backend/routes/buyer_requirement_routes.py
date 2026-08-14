"""
backend/routes/buyer_requirement_routes.py

Buyer requirement CRUD — buyers post what they need.
FR-4: Buyer Requirement Posting
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from backend.services.security import get_current_user
from database.db import Database

router = APIRouter(tags=["Buyer Requirements"])


class BuyerRequirementCreate(BaseModel):
    crop: str = Field(..., example="Wheat")
    quantity: float = Field(..., gt=0, example=1000.0)
    target_price: float = Field(..., gt=0, example=22.0)
    max_price: float = Field(None, example=26.0)
    location: str = Field(..., example="Pune")
    budget: float = Field(..., gt=0, example=30000.0)
    delivery_days: int = Field(7, ge=1, example=7)
    quality_grade: str = Field("A", example="A")
    notes: str = Field("", example="Prefer certified organic")


class BuyerRequirementUpdate(BaseModel):
    quantity: float = None
    target_price: float = None
    max_price: float = None
    budget: float = None
    status: str = None   # "ACTIVE" | "FULFILLED" | "CANCELLED"
    notes: str = None


# In-memory reference mapped directly to Database.requirements cache
_requirements: dict = Database.requirements


@router.get("/")
async def list_requirements(
    crop: str = None,
    location: str = None,
    current_user: dict = Depends(get_current_user),
):
    """Return all active buyer requirements, optionally filtered."""
    reqs = await Database.list_requirements_async(crop=crop, location=location, status="ACTIVE")
    return {"success": True, "data": reqs, "count": len(reqs)}


@router.get("/{requirement_id}")
async def get_requirement(requirement_id: str, current_user: dict = Depends(get_current_user)):
    """Return a specific buyer requirement."""
    req = await Database.get_requirement_async(requirement_id)
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return {"success": True, "data": req}


@router.post("/")
async def create_requirement(
    payload: BuyerRequirementCreate,
    current_user: dict = Depends(get_current_user),
):
    """Post a new buyer requirement."""
    req_id = str(uuid.uuid4())[:12]
    req = {
        "requirement_id": req_id,
        "user_id": current_user["sub"],
        "buyer_name": current_user.get("name", "Buyer"),
        "status": "ACTIVE",
        "created_at": datetime.now(timezone.utc).isoformat(),
        **payload.dict(),
    }
    saved = await Database.upsert_requirement_async(req)
    return {"success": True, "data": saved, "requirement_id": req_id}


@router.patch("/{requirement_id}")
async def update_requirement(
    requirement_id: str,
    payload: BuyerRequirementUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing buyer requirement."""
    req = await Database.get_requirement_async(requirement_id)
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if req["user_id"] != current_user["sub"]:
        raise HTTPException(status_code=403, detail="You do not own this requirement")

    updates = {k: v for k, v in payload.dict().items() if v is not None}
    updated = await Database.update_requirement_async(requirement_id, updates)
    return {"success": True, "data": updated}


@router.delete("/{requirement_id}")
async def cancel_requirement(
    requirement_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Cancel a buyer requirement."""
    req = await Database.get_requirement_async(requirement_id)
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if req["user_id"] != current_user["sub"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="You do not own this requirement")

    await Database.update_requirement_async(requirement_id, {"status": "CANCELLED"})
    return {"success": True, "message": "Requirement cancelled."}
