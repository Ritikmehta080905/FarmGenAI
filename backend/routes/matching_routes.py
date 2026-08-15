"""
backend/routes/matching_routes.py

Matching Engine API endpoints.
FR-5: AI-Powered Farmer-Buyer Matching
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from backend.services.security import get_current_user
from backend.services.matching_service import match_listing_to_buyers, match_requirement_to_listings

router = APIRouter(tags=["Matching"])


class MatchListingRequest(BaseModel):
    listing_id: str = None
    crop: str
    quantity: float = Field(..., gt=0)
    min_price: float = Field(..., gt=0)
    location: str
    spoilage_days: int = Field(7, ge=1)
    quality: str = "A"


class MatchRequirementRequest(BaseModel):
    requirement_id: str = None
    crop: str
    quantity: float = Field(..., gt=0)
    target_price: float = Field(..., gt=0)
    max_price: float = None
    budget: float = Field(..., gt=0)
    location: str


@router.post("/listing-to-buyers")
async def match_listing(
    payload: MatchListingRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Find and rank all buyer requirements compatible with a crop listing.
    Returns scored matches sorted by compatibility.
    """
    listing = payload.dict()
    matches = await match_listing_to_buyers(listing)

    return {
        "success": True,
        "crop": payload.crop,
        "listing_location": payload.location,
        "total_matches": len(matches),
        "grade_a_matches": len([m for m in matches if m["match_grade"] == "A"]),
        "data": matches,
    }


@router.post("/requirement-to-listings")
async def match_requirement(
    payload: MatchRequirementRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Find and rank all crop listings that satisfy a buyer requirement.
    Returns scored matches sorted by compatibility.
    """
    requirement = payload.dict()
    matches = await match_requirement_to_listings(requirement)

    return {
        "success": True,
        "crop": payload.crop,
        "buyer_location": payload.location,
        "total_matches": len(matches),
        "grade_a_matches": len([m for m in matches if m["match_grade"] == "A"]),
        "data": matches,
    }


@router.get("/auto/{listing_id}")
async def auto_match(
    listing_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Automatically match a saved crop listing to buyers using its stored data.
    """
    from database.db import Database
    listing = Database.produce.get(listing_id)
    if not listing:
        # Try listing from produce table
        produce = await Database.list_produce_async()
        listing = next((p for p in produce if p.get("id") == listing_id), None)

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    matches = await match_listing_to_buyers(listing)
    return {
        "success": True,
        "listing_id": listing_id,
        "crop": listing.get("crop"),
        "total_matches": len(matches),
        "data": matches,
    }

