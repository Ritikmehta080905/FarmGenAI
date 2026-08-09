"""
backend/routes/workflow_routes.py

Workflow Planning API endpoints.
FR-6: Automated Workflow Planning & Supply Chain Selection
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from backend.services.security import get_current_user
from backend.services.workflow_service import plan_workflow

router = APIRouter(tags=["Workflow Planning"])


class WorkflowPlanRequest(BaseModel):
    crop: str
    quantity: float = Field(..., gt=0)
    min_price: float = Field(..., gt=0)
    location: str
    spoilage_days: int = Field(..., ge=1)
    market_price: Optional[float] = None
    quality: str = "A"


@router.post("/plan")
async def get_workflow_plan(
    payload: WorkflowPlanRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a supply chain workflow plan for a crop listing.
    Returns ranked options (Direct Sale, Storage, Processing, Composting)
    with the recommended path and financial projections.
    """
    listing = payload.dict()
    plan = plan_workflow(listing, market_price=payload.market_price)
    return {"success": True, "data": plan}


@router.get("/plan/{listing_id}")
async def get_workflow_plan_for_listing(
    listing_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Generate workflow plan for an existing saved crop listing."""
    from database.db import Database
    produce = await Database.list_produce_async()
    listing = next((p for p in produce if p.get("id") == listing_id), None)

    if not listing:
        # Check in-memory crop listings
        from backend.routes.crop_listing_routes import router as _
        if hasattr(Database, "produce") and Database.produce:
            listing = Database.produce.get(listing_id)

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    plan = plan_workflow(listing)
    return {"success": True, "listing_id": listing_id, "data": plan}
