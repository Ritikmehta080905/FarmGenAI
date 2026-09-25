"""
backend/routes/transport_routes.py

Transport booking and fleet management endpoints.
FR-9: Transport Coordination
"""

import uuid
from typing import Optional
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


@router.get("/route-estimate")
async def get_route_estimate(
    origin: str,
    destination: str,
    quantity_kg: float = 1000.0,
    crop: str = "Produce"
):
    """
    Fetch alternate routes from OSRM and calculate estimated market value and floor prices
    for each route. Used to preview real-world costs before booking.
    """
    from backend.services.maps_service import get_alternate_routes
    from backend.services.transport_cost_service import calculate_transportation_cost
    
    # 1. Fetch alternate routes
    route_result = get_alternate_routes(origin, destination)
    if not route_result.get("success"):
        raise HTTPException(status_code=400, detail="Could not calculate routes.")
        
    routes = route_result.get("routes", [])
    
    # Generic vehicle mock based on quantity
    vehicle_type = "Medium Truck"
    if quantity_kg <= 1000:
        vehicle_type = "Mini Truck"
    elif quantity_kg > 8000:
        vehicle_type = "Heavy Truck"
        
    mock_vehicle = {
        "vehicle_type": vehicle_type,
        "fuel_type": "Diesel",
        "fuel_efficiency_kmpl": 8.0 if vehicle_type == "Medium Truck" else (14.0 if vehicle_type == "Mini Truck" else 5.0)
    }
    
    is_perishable = crop.lower() in {"tomato", "banana", "strawberry", "grape", "mango", "milk", "onion"}
    
    # 2. Calculate costs per route
    enriched_routes = []
    best_route_idx = 0
    lowest_cost = float('inf')
    
    for idx, r in enumerate(routes):
        try:
            cost_res = await calculate_transportation_cost(
                vehicle=mock_vehicle,
                distance_km=r["distance_km"],
                estimated_duration_hours=r["duration_hours"],
                deadhead_km=0.0,
                is_perishable=is_perishable
            )
            
            r["estimated_toll"] = cost_res["cost_breakdown"]["toll_cost"]
            r["estimated_fuel"] = cost_res["cost_breakdown"]["fuel_cost"]
            r["floor_price"] = cost_res["minimum_acceptable_price"]
            r["market_average"] = round(cost_res["total_operating_cost"] * 1.20, 2)
            
            if cost_res["total_operating_cost"] < lowest_cost:
                lowest_cost = cost_res["total_operating_cost"]
                best_route_idx = idx
                
        except Exception as e:
            # Fallback if cost calculation fails
            r["estimated_toll"] = round(r["distance_km"] * 2.0, 2)
            r["estimated_fuel"] = round((r["distance_km"] / mock_vehicle["fuel_efficiency_kmpl"]) * 92.5, 2)
            r["floor_price"] = r["estimated_toll"] + r["estimated_fuel"] + 1500
            r["market_average"] = round(r["floor_price"] * 1.30, 2)
            
        r["is_recommended"] = False
        enriched_routes.append(r)
        
    if enriched_routes:
        enriched_routes[best_route_idx]["is_recommended"] = True
        
    return {
        "success": True,
        "origin": origin,
        "destination": destination,
        "vehicle_assumed": vehicle_type,
        "routes": enriched_routes
    }


# ── STANDALONE TRANSPORT AGENT MODULE ENDPOINTS ───────────────────
from backend.schemas.transport_agent_schemas import (
    TransportPlanInput, TransportNegotiationInput, VehicleRegistrationInput
)
from backend.agents.transport_agent.graph import run_transport_workflow, run_transport_negotiation
from backend.services.vehicle_service import get_all_vehicles
from backend.services.fuel_service import get_fuel_price
from backend.services.transport_cost_service import DEFAULT_COST_PARAMS

@router.get("/fuel-estimate")
async def estimate_fuel_and_base_rate(
    fuel_type: str = "Diesel",
    location: str = "Ahmednagar",
    efficiency_kmpl: float = 10.0,
    capacity_kg: float = 5000.0,
    vehicle_type: str = "Medium Truck"
):
    """
    Fetch live fuel price and calculate AI-suggested base rate per km.
    """
    fuel_info = await get_fuel_price(fuel_type, location)
    live_price = fuel_info.get("price_per_litre", 90.0)

    # Simple cost formula per km
    fuel_cost_per_km = live_price / efficiency_kmpl if efficiency_kmpl > 0 else 0
    
    # Toll estimates based on vehicle size
    toll_per_km = 2.0
    if vehicle_type == "Mini Truck":
        toll_per_km = 1.2
    elif vehicle_type == "Heavy Truck":
        toll_per_km = 3.0
    elif vehicle_type == "Cargo Three-Wheeler":
        toll_per_km = 0.0
        
    maintenance_per_km = 5.0
    driver_per_km = 4.0 # roughly assuming 200/hr and 50km/hr
    
    total_cost_per_km = fuel_cost_per_km + toll_per_km + maintenance_per_km + driver_per_km
    suggested_rate = round(total_cost_per_km * 1.20, 2) # Add 20% margin

    return {
        "success": True,
        "fuel_price": live_price,
        "fuel_type": fuel_type,
        "location": fuel_info.get("location"),
        "is_estimate": fuel_info.get("is_estimate"),
        "suggested_rate_per_km": suggested_rate
    }

@router.post("/plan")
async def create_transport_plan(payload: TransportPlanInput):
    """
    Run full LangGraph Transport Agent workflow for a standalone transport requirement.
    Uses OSRM routing and deterministic cost calculation engine.
    """
    req_dict = payload.model_dump()
    state_result = await run_transport_workflow(req_dict)

    if not state_result.get("is_valid_request", True):
        raise HTTPException(status_code=400, detail=state_result.get("validation_error", "Invalid transport request"))

    plan = state_result.get("final_transport_plan")
    if not plan or state_result.get("status") in ("INFEASIBLE", "FAILED") or not state_result.get("selected_vehicle"):
        return {
            "success": False,
            "status": "INFEASIBLE",
            "message": "No vehicle available matching requested quantity and hard constraints.",
            "rejected_vehicles": state_result.get("rejected_vehicles", []),
            "logs": state_result.get("logs", [])
        }

    if plan and plan.get("vehicle_id"):
        # Save trip record asynchronously
        await Database.save_transport_trip_async({
            "request_id": plan.get("request_id"),
            "vehicle_id": plan.get("vehicle_id"),
            "vehicle_type": plan.get("vehicle_type"),
            "crop": plan.get("crop"),
            "quantity_kg": plan.get("quantity_kg"),
            "pickup_location": plan.get("pickup_location"),
            "delivery_location": plan.get("delivery_location"),
            "distance_km": plan.get("distance_km"),
            "estimated_duration_hours": plan.get("estimated_duration_hours"),
            "fuel_cost": plan.get("cost_breakdown", {}).get("fuel_cost", 0.0),
            "toll_cost": plan.get("cost_breakdown", {}).get("toll_cost", 0.0),
            "driver_cost": plan.get("cost_breakdown", {}).get("driver_cost", 0.0),
            "maintenance_cost": plan.get("cost_breakdown", {}).get("maintenance_cost", 0.0),
            "loading_cost": plan.get("cost_breakdown", {}).get("loading_cost", 0.0),
            "waiting_cost": plan.get("cost_breakdown", {}).get("waiting_cost", 0.0),
            "total_operating_cost": plan.get("total_operating_cost"),
            "minimum_acceptable_price": plan.get("minimum_acceptable_price"),
            "agreed_price": plan.get("agreed_price"),
            "expected_profit": plan.get("expected_profit"),
            "status": plan.get("status", "CONFIRMED"),
            "details_json": plan,
            "created_at": datetime.now(timezone.utc).isoformat()
        })

    return {
        "success": True,
        "data": plan,
        "full_state": state_result
    }


@router.post("/negotiate")
async def negotiate_transport_price(payload: TransportNegotiationInput):
    """
    Run an interactive negotiation turn with the Transport Agent.
    Evaluates buyer offer against deterministic floor price and returns agent counter/decision.
    """
    updated_state = await run_transport_negotiation(
        current_state_dict=payload.state,
        buyer_offer=payload.buyer_offer
    )
    return {
        "success": True,
        "negotiation_status": updated_state.get("negotiation_status"),
        "agent_counter_offer": updated_state.get("agent_counter_offer"),
        "agreed_price": updated_state.get("agreed_price"),
        "explanation": updated_state.get("llm_explanation"),
        "plan": updated_state.get("final_transport_plan"),
        "state": updated_state
    }


@router.post("/requests")
async def submit_transport_request(payload: TransportPlanInput):
    """Submit a standalone transport request and generate initial quote."""
    return await create_transport_plan(payload)


@router.get("/vehicles")
async def list_transport_vehicles(status: Optional[str] = "AVAILABLE"):
    """List registered transport vehicles and current status."""
    vehicles = await get_all_vehicles(status_filter=status)
    return {"success": True, "count": len(vehicles), "data": vehicles}


@router.post("/vehicles")
async def register_transport_vehicle(
    payload: VehicleRegistrationInput,
    current_user: dict = Depends(get_current_user)
):
    """Register a new vehicle in the transport fleet."""
    v_dict = payload.model_dump()
    v_id = f"veh_{uuid.uuid4().hex[:6]}"
    v_dict["vehicle_id"] = v_id
    v_dict["status"] = "AVAILABLE"
    
    # Map 'transporter_id' to the logged-in user ID so they can own this vehicle
    v_dict["transporter_id"] = current_user.get("sub", "unknown")

    # Add to DB
    from backend.db.session import AsyncSessionLocal
    from backend.db.models.transport_agent_models import DBVehicle
    async with AsyncSessionLocal() as session:
        db_veh = DBVehicle(**v_dict)
        session.add(db_veh)
        await session.commit()

    return {"success": True, "data": v_dict}


@router.get("/trips")
async def list_transport_trips(limit: int = 50):
    """List recent completed and active transport trips."""
    trips = await Database.list_transport_trips_async(limit=limit)
    return {"success": True, "count": len(trips), "data": trips}


@router.get("/trips/{trip_id}")
async def get_transport_trip_details(trip_id: str):
    """Fetch stored details of a transport trip."""
    trip = await Database.get_transport_trip_async(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Transport trip not found")
    return {"success": True, "data": trip}


@router.get("/parameters")
async def get_transport_cost_parameters():
    """Retrieve cost calculation parameters and active fuel price benchmarks."""
    fuel_info = await get_fuel_price("Diesel", "Maharashtra")
    return {
        "success": True,
        "fuel_benchmark": fuel_info,
        "cost_parameters": DEFAULT_COST_PARAMS
    }

