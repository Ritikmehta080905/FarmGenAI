"""
backend/routes/transport_routes.py

Transport booking and fleet management endpoints.
FR-9: Transport Coordination
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from backend.services.security import get_current_user
from backend.services.transport_service import list_fleet, assign_transport
from backend.schemas.transport_model import TransportBookingRequest, TransportStatusUpdate

router = APIRouter(tags=["Transport"])

from database.db import Database

@router.get("/fleet")
async def get_fleet(current_user: dict = Depends(get_current_user)):
    """List all available transport vehicles."""
    fleet = await list_fleet()
    return {"success": True, "data": fleet, "count": len(fleet)}


@router.post("/book")
async def book_transport(
    payload: TransportBookingRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Book a transport vehicle for a negotiation shipment.
    Automatically selects optimal vehicle based on quantity and distance.
    """
    try:
        assignment = await assign_transport({
            "quantity": payload.quantity,
            "distance_km": payload.distance_km,
            "shelf_life": payload.shelf_life,
            "crop": payload.crop,
            "origin": payload.origin_location,
            "destination": payload.destination_location,
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    booking_id = f"booking_{str(uuid.uuid4())[:8]}"
    booking = {
        "booking_id": booking_id,
        "negotiation_id": payload.negotiation_id,
        "crop": payload.crop,
        "origin_location": payload.origin_location,
        "destination_location": payload.destination_location,
        "booked_by": current_user["sub"],
        "status": "SCHEDULED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        **assignment,
    }
    await Database.create_booking_async(booking)
    return {"success": True, "data": booking}


@router.get("/booking/{booking_id}")
async def get_booking(booking_id: str, current_user: dict = Depends(get_current_user)):
    """Get transport booking details."""
    booking = await Database.get_booking_async(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"success": True, "data": booking}


@router.get("/track/{booking_id}")
async def track_booking(booking_id: str, current_user: dict = Depends(get_current_user)):
    """Alias for getting booking details."""
    return await get_booking(booking_id, current_user)


@router.get("/bookings")
async def list_bookings(current_user: dict = Depends(get_current_user)):
    """List transport bookings for the current user."""
    uid = current_user["sub"]
    all_bookings = await Database.list_bookings_async()
    my_bookings = [b for b in all_bookings if b.get("booked_by") == uid]
    return {"success": True, "data": my_bookings, "count": len(my_bookings)}


@router.patch("/booking/{booking_id}/status")
async def update_booking_status(
    booking_id: str,
    payload: TransportStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update transport booking status (e.g., IN_TRANSIT, DELIVERED)."""
    booking = await Database.get_booking_async(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    valid_statuses = {"SCHEDULED", "IN_TRANSIT", "DELIVERED", "CANCELLED"}
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    update_payload = {
        "status": payload.status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await Database.update_booking_async(booking_id, update_payload)
    booking.update(update_payload)
    return {"success": True, "data": booking}


@router.patch("/status/{booking_id}")
async def update_booking_status_alias(
    booking_id: str,
    payload: TransportStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Alias for updating booking status."""
    return await update_booking_status(booking_id, payload, current_user)


@router.get("/estimate")
async def estimate_transport_cost(
    quantity: float = 100.0,
    distance_km: float = 60.0,
    shelf_life: int = 3,
    current_user: dict = Depends(get_current_user),
):
    """Quick cost estimate without booking."""
    try:
        result = await assign_transport({
            "quantity": quantity,
            "distance_km": distance_km,
            "shelf_life": shelf_life,
        })
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

