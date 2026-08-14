"""
backend/routes/crop_listing_routes.py

Crop listing CRUD — farmers post produce availability.
FR-3: Farmer Crop Listing Management
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from backend.services.security import get_current_user
from database.db import Database

router = APIRouter(tags=["Crop Listings"])


class CropListingCreate(BaseModel):
    crop: str = Field(..., example="Tomato")
    quantity: float = Field(..., gt=0, example=500.0)
    min_price: float = Field(..., gt=0, example=18.0)
    location: str = Field(..., example="Nashik")
    spoilage_days: int = Field(..., ge=1, example=7)
    description: str = Field("", example="Organic grade A")


class CropListingUpdate(BaseModel):
    quantity: float = None
    min_price: float = None
    spoilage_days: int = None
    description: str = None
    status: str = None  # "ACTIVE" | "SOLD" | "EXPIRED"


@router.get("")
@router.get("/")
async def list_crop_listings(
    crop: str = None,
    location: str = None,
    current_user: dict = Depends(get_current_user),
):
    """Return all active crop listings, optionally filtered."""
    listings = list(Database.produce.values()) if hasattr(Database, "produce") else []
    if crop:
        listings = [l for l in listings if l.get("crop", "").lower() == crop.lower()]
    if location:
        listings = [l for l in listings if l.get("location", "").lower() == location.lower()]
    return {"success": True, "data": listings, "count": len(listings)}


@router.get("/me")
async def get_my_crop_listings(current_user: dict = Depends(get_current_user)):
    """Return all active crop listings owned by the authenticated farmer formatted for the frontend."""
    listings = list(Database.produce.values()) if hasattr(Database, "produce") and Database.produce else []
    my_listings = [
        l for l in listings 
        if l.get("user_id") == current_user.get("sub") or l.get("user_id") == current_user.get("user_id")
    ]
    formatted = [
        {
            "id": l.get("listing_id") or l.get("id"),
            "listing_id": l.get("listing_id") or l.get("id"),
            "crop": l.get("crop"),
            "qty": l.get("quantity") or l.get("qty", 0),
            "quantity": l.get("quantity") or l.get("qty", 0),
            "price": l.get("min_price") or l.get("price", 0),
            "min_price": l.get("min_price") or l.get("price", 0),
            "status": l.get("status", "ACTIVE"),
            "location": l.get("location", ""),
            "spoilage_days": l.get("spoilage_days", 7)
        }
        for l in my_listings
    ]
    return formatted


@router.get("/{listing_id}")
async def get_crop_listing(listing_id: str, current_user: dict = Depends(get_current_user)):
    """Return a specific crop listing."""
    listing = Database.produce.get(listing_id) if hasattr(Database, "produce") else None
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {"success": True, "data": listing}


@router.post("")
@router.post("/")
async def create_crop_listing(
    payload: CropListingCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new crop listing for the authenticated farmer."""
    listing_id = str(uuid.uuid4())[:12]
    listing = {
        "listing_id": listing_id,
        "user_id": current_user["sub"],
        "farmer_name": current_user.get("name", "Farmer"),
        "status": "ACTIVE",
        "created_at": datetime.now(timezone.utc).isoformat(),
        **payload.dict(),
    }
    if not hasattr(Database, "produce") or Database.produce is None:
        Database.produce = {}
    Database.produce[listing_id] = listing
    return {"success": True, "data": listing, "listing_id": listing_id}


@router.patch("/{listing_id}")
async def update_crop_listing(
    listing_id: str,
    payload: CropListingUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing crop listing. Only the owner can update."""
    if not hasattr(Database, "produce") or not Database.produce:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing = Database.produce.get(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing["user_id"] != current_user["sub"]:
        raise HTTPException(status_code=403, detail="You do not own this listing")

    updates = {k: v for k, v in payload.dict().items() if v is not None}
    listing.update(updates)
    listing["updated_at"] = datetime.now(timezone.utc).isoformat()
    Database.produce[listing_id] = listing
    return {"success": True, "data": listing}


@router.delete("/{listing_id}")
async def delete_crop_listing(
    listing_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete (expire) a crop listing."""
    if not hasattr(Database, "produce") or not Database.produce:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing = Database.produce.get(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing["user_id"] != current_user["sub"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="You do not own this listing")

    listing["status"] = "EXPIRED"
    Database.produce[listing_id] = listing
    return {"success": True, "message": "Listing marked as expired."}
