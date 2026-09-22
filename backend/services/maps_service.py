"""
backend/services/maps_service.py

OSRM (Open Source Routing Machine) & OpenStreetMap routing service.
Used by Transporter Agent and Matching Engine for real-time driving distances and transit times.

No API key required.
Demo Server: https://router.project-osrm.org
"""

import logging
import requests
from typing import Dict, Any
from backend.services.weather_service import CITY_COORDINATES

logger = logging.getLogger("MapsService")

OSRM_BASE_URL = "https://router.project-osrm.org"


def get_route_distance_and_duration(origin: str, destination: str) -> Dict[str, Any]:
    """
    Calculate driving distance (in km) and duration (in hours) between two cities
    using the public OSRM routing engine API.
    """
    orig_coords = CITY_COORDINATES.get(origin, CITY_COORDINATES.get("Nashik"))
    dest_coords = CITY_COORDINATES.get(destination, CITY_COORDINATES.get("Mumbai"))

    # Format: lon1,lat1;lon2,lat2
    coordinates_str = f"{orig_coords['lon']},{orig_coords['lat']};{dest_coords['lon']},{dest_coords['lat']}"
    url = f"{OSRM_BASE_URL}/route/v1/driving/{coordinates_str}?overview=false"

    try:
        response = requests.get(url, timeout=4)
        if response.status_code == 200:
            routes = response.json().get("routes", [])
            if routes:
                route = routes[0]
                distance_km = round(route.get("distance", 0) / 1000.0, 2)
                duration_hours = round(route.get("duration", 0) / 3600.0, 2)

                route_mapping = {
                    "pune-mumbai": ["Pune", "Lonavala", "Navi Mumbai", "Mumbai"],
                    "ahmednagar-pune": ["Ahmednagar", "Shirur", "Wagholi", "Pune"],
                    "nashik-mumbai": ["Nashik", "Igatpuri", "Thane", "Mumbai"],
                    "nagpur-pune": ["Nagpur", "Amravati", "Aurangabad", "Pune"]
                }
                
                via_cities = [origin, "Main Highway", destination]
                route_key = f"{origin.lower()}-{destination.lower()}"
                if route_key in route_mapping:
                    via_cities = route_mapping[route_key]
                elif f"{destination.lower()}-{origin.lower()}" in route_mapping:
                    via_cities = list(reversed(route_mapping[f"{destination.lower()}-{origin.lower()}"]))
                
                route_path = " ➔ ".join(via_cities)

                return {
                    "success": True,
                    "origin": origin,
                    "destination": destination,
                    "distance_km": distance_km,
                    "duration_hours": duration_hours,
                    "route_path": route_path,
                    "source": "OSRM Routing Engine",
                }
    except Exception as e:
        logger.warning(f"OSRM routing request failed for {origin} -> {destination}: {e}. Falling back to Haversine matrix.")

    # Failsafe fallback distance matrix
    from backend.services.matching_service import CITY_DISTANCES_KM
    orig_clean = (origin or "").strip()
    dest_clean = (destination or "").strip()
    fallback_dist = CITY_DISTANCES_KM.get(orig_clean, {}).get(dest_clean)
    if fallback_dist is None:
        fallback_dist = CITY_DISTANCES_KM.get(dest_clean, {}).get(orig_clean, 150.0 if orig_clean != dest_clean else 0.0)
    fallback_dist = float(fallback_dist)
    fallback_duration = round(fallback_dist / 35.0, 2)  # Avg 35 km/h truck speed

    return {
        "success": True,
        "origin": origin,
        "destination": destination,
        "distance_km": fallback_dist,
        "duration_hours": fallback_duration,
        "route_path": f"{origin} ➔ Highway ➔ {destination}",
        "source": "Fallback Distance Matrix",
    }


def get_alternate_routes(origin: str, destination: str) -> Dict[str, Any]:
    """
    Calculate multiple driving routes between two cities using OSRM.
    Returns up to 3 alternate routes.
    """
    orig_coords = CITY_COORDINATES.get(origin, CITY_COORDINATES.get("Nashik"))
    dest_coords = CITY_COORDINATES.get(destination, CITY_COORDINATES.get("Mumbai"))

    coordinates_str = f"{orig_coords['lon']},{orig_coords['lat']};{dest_coords['lon']},{dest_coords['lat']}"
    url = f"{OSRM_BASE_URL}/route/v1/driving/{coordinates_str}?overview=false&alternatives=true"

    try:
        response = requests.get(url, timeout=4)
        if response.status_code == 200:
            routes_data = response.json().get("routes", [])
            parsed_routes = []
            
            for idx, route in enumerate(routes_data):
                dist_km = round(route.get("distance", 0) / 1000.0, 2)
                dur_hrs = round(route.get("duration", 0) / 3600.0, 2)
                
                # Determine route name based on typical Indian highways or generic fallback
                route_name = f"Route {idx + 1}"
                via_cities = []
                
                if idx == 0:
                    route_name = "Primary Route (Fastest)"
                    via_cities = [origin, "Main Highway", destination]
                elif idx == 1:
                    route_name = "Alternate Route (State Highway)"
                    via_cities = [origin, "State Route", destination]
                else:
                    route_name = "Alternate Route 2"
                    via_cities = [origin, "Bypass Road", destination]
                    
                # Enhance realistic Indian routes for the demo
                route_mapping = {
                    "pune-mumbai": [["Pune", "Lonavala", "Navi Mumbai", "Mumbai"], ["Pune", "Panvel", "Mumbai"]],
                    "ahmednagar-pune": [["Ahmednagar", "Shirur", "Wagholi", "Pune"], ["Ahmednagar", "Kondhapuri", "Pune"]],
                    "nashik-mumbai": [["Nashik", "Igatpuri", "Thane", "Mumbai"], ["Nashik", "Kasara", "Mumbai"]],
                    "nagpur-pune": [["Nagpur", "Amravati", "Aurangabad", "Pune"], ["Nagpur", "Wardha", "Jalna", "Pune"]]
                }
                
                route_key = f"{origin.lower()}-{destination.lower()}"
                if route_key in route_mapping:
                    options = route_mapping[route_key]
                    via_cities = options[idx % len(options)]
                elif f"{destination.lower()}-{origin.lower()}" in route_mapping:
                    options = route_mapping[f"{destination.lower()}-{origin.lower()}"]
                    via_cities = list(reversed(options[idx % len(options)]))
                
                route_path = " ➔ ".join(via_cities)
                    
                parsed_routes.append({
                    "route_id": f"route_{idx}",
                    "name": route_name,
                    "distance_km": dist_km,
                    "duration_hours": dur_hrs,
                    "route_path": route_path
                })

            if parsed_routes:
                return {
                    "success": True,
                    "origin": origin,
                    "destination": destination,
                    "routes": parsed_routes
                }
    except Exception as e:
        logger.warning(f"OSRM alternate routing failed for {origin} -> {destination}: {e}")

    # Fallback to single route matrix
    fallback_route = get_route_distance_and_duration(origin, destination)
    return {
        "success": True,
        "origin": origin,
        "destination": destination,
        "routes": [{
            "route_id": "route_fallback",
            "name": "Standard Route",
            "distance_km": fallback_route.get("distance_km", 150),
            "duration_hours": fallback_route.get("duration_hours", 4.0),
            "route_path": f"{origin} ➔ Highway ➔ {destination}"
        }]
    }

