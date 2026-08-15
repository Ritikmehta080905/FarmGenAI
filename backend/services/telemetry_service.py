"""
backend/services/telemetry_service.py

Telemetry adapters for weather information (Open-Meteo API)
and transit logistics/routing (OSRM Project API).
"""

import logging
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TelemetryService")

# Regional Maharashtra coordinates lookup (Lat, Lon)
MAHARASHTRA_COORDINATES = {
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Nashik": (19.9975, 73.7898),
    "Nagpur": (21.1458, 79.0882),
    "Satara": (17.6805, 73.9918),
    "Ahmednagar": (19.0948, 74.7480),
    "Kolhapur": (16.7050, 74.2433),
    "Solapur": (17.6599, 75.9064),
    "Aurangabad": (19.8762, 75.3433),
    "Thane": (19.2183, 72.9781),
    "Kalyan": (19.2403, 73.1305)
}


class TelemetryService:
    """External telemetry integration service for weather and logistics API adapters."""
    
    async def get_weather(self, city: str) -> dict:
        """Fetch current weather from Open-Meteo API, with robust default fallback."""
        coords = MAHARASHTRA_COORDINATES.get(city)
        if not coords:
            return {"temperature": 27.5, "condition": "Sunny", "humidity": 60}
        
        lat, lon = coords
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        try:
            r = requests.get(url, timeout=3.0)
            if r.status_code == 200:
                data = r.json().get("current_weather", {})
                return {
                    "temperature": data.get("temperature", 27.5),
                    "condition": "Clear" if data.get("weathercode", 0) == 0 else "Cloudy",
                    "windspeed": data.get("windspeed", 10.0)
                }
        except Exception as e:
            logger.warning(f"Failed to fetch live weather from Open-Meteo: {e}. Using default fallback.")
            
        return {"temperature": 28.0, "condition": "Sunny", "humidity": 65}

    async def calculate_distance(self, from_city: str, to_city: str) -> dict:
        """Compute road distance and travel duration via OSRM, with math geo-approximation fallback."""
        loc1 = MAHARASHTRA_COORDINATES.get(from_city)
        loc2 = MAHARASHTRA_COORDINATES.get(to_city)
        
        if not loc1 or not loc2:
            return {"distance_km": 150.0, "duration_hours": 3.0}
            
        # OSRM coordinate coordinates format: longitude,latitude
        coords_str = f"{loc1[1]},{loc1[0]};{loc2[1]},{loc2[0]}"
        url = f"http://router.project-osrm.org/route/v1/driving/{coords_str}?overview=false"
        try:
            r = requests.get(url, timeout=3.0)
            if r.status_code == 200:
                routes = r.json().get("routes", [])
                if routes:
                    route = routes[0]
                    # convert meters to km, seconds to hours
                    return {
                        "distance_km": round(route.get("distance", 150000) / 1000.0, 2),
                        "duration_hours": round(route.get("duration", 10800) / 3600.0, 2)
                    }
        except Exception as e:
            logger.warning(f"Failed to fetch live logistics from OSRM: {e}. Using geo-fallback.")

        # Haversine distance geo-fallback approximation
        import math
        lat1, lon1 = math.radians(loc1[0]), math.radians(loc1[1])
        lat2, lon2 = math.radians(loc2[0]), math.radians(loc2[1])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371.0 # Earth radius in km
        dist_direct = c * r
        # Add road scaling factor (usually ~1.25x direct path)
        dist_road = round(dist_direct * 1.25, 2)
        # Average velocity assumption (50 km/h)
        duration = round(dist_road / 50.0, 2)
        return {
            "distance_km": dist_road,
            "duration_hours": duration
        }


# Singleton instance
telemetry_service = TelemetryService()

