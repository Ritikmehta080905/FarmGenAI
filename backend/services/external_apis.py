import json
import logging
import random
from typing import Dict, Any, Optional
import urllib.request
import urllib.parse
import urllib.error

logger = logging.getLogger("backend.services.external_apis")

async def _geocode(location: str) -> Optional[Dict[str, float]]:
    import asyncio
    loop = asyncio.get_event_loop()
    
    def _fetch():
        try:
            safe_location = urllib.parse.quote(location)
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={safe_location}&count=1"
            req = urllib.request.Request(geo_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                geo_data = json.loads(response.read().decode())
            if not geo_data.get("results"):
                return None
            return {
                "latitude": geo_data["results"][0]["latitude"],
                "longitude": geo_data["results"][0]["longitude"],
                "name": geo_data["results"][0]["name"]
            }
        except Exception as e:
            logger.error(f"Geocoding error for {location}: {e}")
            return None
    return await loop.run_in_executor(None, _fetch)

class OpenMeteoClient:
    """
    Client for fetching real-time weather data from the open-meteo API.
    Does not require an API key.
    """
    @staticmethod
    async def get_weather(location: str) -> Optional[Dict[str, Any]]:
        import asyncio
        loop = asyncio.get_event_loop()
        
        # Geocode first
        coords = await _geocode(location)
        if not coords:
            logger.warning(f"No geocoding results found for {location}")
            return None
            
        lat = coords["latitude"]
        lon = coords["longitude"]
        
        def _fetch():
            try:
                weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,wind_speed_10m"
                req = urllib.request.Request(weather_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    weather_data = json.loads(response.read().decode())
                    
                current = weather_data.get("current", {})
                return {
                    "temperature_c": current.get("temperature_2m"),
                    "precipitation_mm": current.get("precipitation"),
                    "wind_speed_kmh": current.get("wind_speed_10m"),
                    "location_resolved": coords["name"]
                }
            except Exception as e:
                logger.error(f"Error fetching weather for {location}: {e}")
                return None
                
        return await loop.run_in_executor(None, _fetch)
class MandiAPIClient:
    """
    Simulated wrapper for the Indian Government Agmarknet API.
    In a real-world scenario, this would authenticate using an API key and fetch SOAP/XML.
    Here we simulate a live fetch by generating location-adjusted modal prices.
    """
    @staticmethod
    async def get_live_price(crop: str, location: str, base_market_price: float) -> Dict[str, Any]:
        # Simulate network delay (would be async sleep in real world)
        import asyncio
        await asyncio.sleep(0.5)
        
        # Add random volatility (-5% to +5%) to the base market price to simulate live fluctuations
        volatility = random.uniform(-0.05, 0.05)
        live_price = base_market_price * (1 + volatility)
        
        # Determine trend
        if volatility > 0.02:
            trend = "Bullish"
        elif volatility < -0.02:
            trend = "Bearish"
        else:
            trend = "Stable"
            
        return {
            "source": "Agmarknet (Simulated)",
            "crop": crop,
            "mandi": f"{location} APMC",
            "live_modal_price": round(live_price, 2),
            "trend": trend,
            "volatility_pct": round(volatility * 100, 2),
            "timestamp": "Real-time"
        }

class OSRMClient:
    """
    Client for fetching driving distances via the open-source OSRM routing API.
    Provides free routing without API keys.
    """
    @staticmethod
    async def get_driving_distance_km(source: str, destination: str) -> Optional[float]:
        import asyncio
        loop = asyncio.get_event_loop()
        
        # 1. Geocode both points
        src_coords = await _geocode(source)
        dst_coords = await _geocode(destination)
        
        if not src_coords or not dst_coords:
            logger.warning(f"Could not geocode locations for routing: {source} -> {destination}")
            return None
            
        def _fetch_route():
            try:
                # OSRM expects lon,lat format
                coords = f"{src_coords['longitude']},{src_coords['latitude']};{dst_coords['longitude']},{dst_coords['latitude']}"
                osrm_url = f"http://router.project-osrm.org/route/v1/driving/{coords}?overview=false"
                req = urllib.request.Request(osrm_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    route_data = json.loads(response.read().decode())
                    
                if route_data.get("code") == "Ok" and route_data.get("routes"):
                    distance_meters = route_data["routes"][0]["distance"]
                    return distance_meters / 1000.0  # Convert to KM
                return None
            except Exception as e:
                logger.error(f"Error fetching route {source} -> {destination}: {e}")
                return None
                
        return await loop.run_in_executor(None, _fetch_route)
