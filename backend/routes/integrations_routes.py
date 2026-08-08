"""
backend/routes/integrations_routes.py

API endpoints for external service integrations:
- Weather API (Open-Meteo)
- Maps & Distance API (OSRM)
- Mandi Prices & MSP (AGMARKNET)
- Object Storage (MinIO)
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from backend.services.security import get_current_user
from backend.services.weather_service import get_current_weather, predict_spoilage_acceleration
from backend.services.maps_service import get_route_distance_and_duration
from backend.services.market_price_service import get_crop_market_price, list_all_market_prices
from backend.services.storage_object_service import object_storage_service

router = APIRouter(tags=["Integrations"])


# ── Weather (Open-Meteo) ─────────────────────────

@router.get("/weather")
async def get_weather(location: str = "Nashik", current_user: dict = Depends(get_current_user)):
    """Fetch live/forecast weather metrics from Open-Meteo."""
    return get_current_weather(location)


@router.get("/weather/spoilage-risk")
async def get_spoilage_risk(
    crop: str,
    shelf_life_days: int = 5,
    location: str = "Nashik",
    current_user: dict = Depends(get_current_user),
):
    """Predict weather-accelerated produce spoilage risk."""
    return predict_spoilage_acceleration(crop, shelf_life_days, location)


# ── Maps & Routing (OSRM) ────────────────────────

@router.get("/maps/route")
async def get_route(
    origin: str = "Nashik",
    destination: str = "Mumbai",
    current_user: dict = Depends(get_current_user),
):
    """Calculate driving distance (km) and transit duration (hours) via OSRM."""
    return get_route_distance_and_duration(origin, destination)


# ── Mandi Prices (AGMARKNET) ─────────────────────

@router.get("/mandi/prices")
async def get_mandi_prices(crop: str = None, location: str = "Nashik", current_user: dict = Depends(get_current_user)):
    """Fetch Mandi price benchmarks and Minimum Support Price (MSP)."""
    if crop:
        return get_crop_market_price(crop, location)
    return {"success": True, "data": list_all_market_prices()}


# ── Object Storage (MinIO) ───────────────────────

@router.post("/storage/upload")
async def upload_document(
    bucket: str = "documents",
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload verification document or crop image to MinIO / object store."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    result = object_storage_service.upload_file(
        bucket_name=bucket,
        file_name=file.filename,
        file_data=data,
        content_type=file.content_type or "application/octet-stream",
    )
    return result
