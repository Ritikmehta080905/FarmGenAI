import logging
from typing import List, Dict, Any
from backend.services.routing_service import calculate_transport_route

logger = logging.getLogger("RecommendationService")

def score_vehicle(vehicle: Dict[str, Any], transport_request: Dict[str, Any]) -> float:
    """
    Computes a recommendation score for a given vehicle based on transport request parameters.
    Higher score is better.
    """
    # Weights
    W_DIST = 0.3
    W_SHELF = 0.2
    W_URGENCY = 0.2
    W_CAP = 0.15
    W_REFRIG = 0.15

    # Factors
    pickup_location = transport_request.get("pickup_location", "Ahmednagar")
    delivery_location = transport_request.get("delivery_location", "Pune")
    vehicle_location = vehicle.get("current_location", pickup_location)

    # 1. Distance (deadhead to pickup + pickup to delivery)
    try:
        route_info = calculate_transport_route(
            pickup_location=pickup_location,
            delivery_location=delivery_location,
            vehicle_current_location=vehicle_location
        )
        total_distance = route_info.get("distance_km", 50.0) + route_info.get("deadhead_km", 0.0)
    except Exception as e:
        logger.error(f"Routing failed in recommendation: {e}")
        total_distance = 100.0 # fallback

    distance_score = 100 / max(total_distance, 1.0)  # Inverse relation

    # 2. Shelf Life Factor
    shelf_life_hours = float(transport_request.get("shelf_life_hours", 24.0))
    is_perishable = transport_request.get("crop", "").lower() in {"tomato", "banana", "strawberry", "grape", "mango", "milk"}
    shelf_life_factor = 1.0 if (shelf_life_hours > 48 and not is_perishable) else (50.0 / max(shelf_life_hours, 1.0))
    
    # 3. Urgency Factor
    urgency = transport_request.get("urgency", "NORMAL").upper()
    urgency_factor = 1.5 if urgency == "HIGH" else (1.0 if urgency == "NORMAL" else 0.5)

    # 4. Capacity Factor
    req_capacity = float(transport_request.get("quantity_kg", 1000.0))
    veh_capacity = float(vehicle.get("capacity_kg", 1000.0))
    # We want vehicles that match closely or are slightly larger
    capacity_ratio = veh_capacity / req_capacity if req_capacity > 0 else 1.0
    if capacity_ratio < 1.0:
        capacity_factor = 0.0  # Invalid, too small
    else:
        # Score peaks at 1.0 and decays as the vehicle gets too large (inefficient)
        capacity_factor = max(0.0, 2.0 - capacity_ratio) 

    # 5. Refrigeration
    req_refrig = transport_request.get("refrigerated_required", False) or is_perishable
    veh_refrig = vehicle.get("refrigerated", False)
    refrig_factor = 1.0 if (req_refrig and veh_refrig) else (0.5 if not req_refrig else 0.0)

    score = (W_DIST * distance_score) + (W_SHELF * shelf_life_factor) + (W_URGENCY * urgency_factor) + (W_CAP * capacity_factor) + (W_REFRIG * refrig_factor)
    return float(score)

def recommend_vehicles_for_request(candidate_vehicles: List[Dict[str, Any]], transport_request: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Ranks a list of candidate vehicles for a given transport request.
    Returns the list sorted by score descending.
    """
    scored_vehicles = []
    for v in candidate_vehicles:
        # Avoid modifying original vehicle dict if possible
        v_copy = dict(v)
        score = score_vehicle(v_copy, transport_request)
        v_copy["recommendation_score"] = score
        scored_vehicles.append(v_copy)
    
    # Sort descending by score
    scored_vehicles.sort(key=lambda x: x.get("recommendation_score", 0.0), reverse=True)
    return scored_vehicles
