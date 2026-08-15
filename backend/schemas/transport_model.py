"""
backend/models/transport_model.py

Pydantic schemas for Transport booking and tracking.
"""

from pydantic import BaseModel, Field
from typing import Optional


class TransportBookingRequest(BaseModel):
    negotiation_id: str
    crop: str
    quantity: float = Field(..., gt=0)
    origin_location: str
    destination_location: str
    distance_km: float = Field(60.0, gt=0)
    shelf_life: int = Field(3, ge=1)
    preferred_pickup_time: Optional[str] = None


class TransportBookingResponse(BaseModel):
    booking_id: str
    negotiation_id: str
    vehicle_id: str
    truck: str
    quantity: float
    distance_km: float
    pickup_time: str
    estimated_transit_hours: int
    estimated_cost: float
    status: str


class TransportStatusUpdate(BaseModel):
    status: str  # SCHEDULED | IN_TRANSIT | DELIVERED | CANCELLED


class TransportListResponse(BaseModel):
    vehicles: list
    count: int

