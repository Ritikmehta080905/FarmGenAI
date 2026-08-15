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
    Wrapper for the Indian Government Agmarknet API via data.gov.in.
    Fetches real-time modal prices for a given crop and location.
    Provides a mathematical fallback to simulated volatility if the API key is missing
    or the external network request fails.
    """
    @staticmethod
    async def get_live_price(crop: str, location: str, base_market_price: float) -> Dict[str, Any]:
        from backend.services.rag_service import rag_service
        try:
            res = await rag_service.query_mandi_records(
                query_text=f"Live market price for {crop} in {location}",
                n_results=1,
                crop=crop
            )
            
            if res and res.get("documents") and len(res["documents"]) > 0 and len(res["documents"][0]) > 0:
                doc = res["documents"][0][0]
                meta = res["metadatas"][0][0]
                
                modal_price_per_quintal = meta.get("modal_price", 0)
                if modal_price_per_quintal > 0:
                    live_price = modal_price_per_quintal / 100.0
                    volatility = (live_price - base_market_price) / base_market_price if base_market_price else 0
                    trend = "Bullish" if volatility > 0.02 else "Bearish" if volatility < -0.02 else "Stable"
                    
                    return {
                        "source": "Agmarknet (Chroma DB)",
                        "crop": crop,
                        "location": location,
                        "mandi": meta.get("mandi", location),
                        "live_modal_price": round(live_price, 2),
                        "trend": trend,
                        "volatility_pct": round(volatility * 100, 2),
                        "raw_data": doc
                    }
        except Exception as e:
            logger.warning(f"Failed to fetch live Mandi price from RAG: {e}")

        # Fallback mathematical simulation if crop not in our DB
        import random
        volatility = random.uniform(-0.15, 0.15)
        live_price = base_market_price * (1 + volatility) if base_market_price else 100
        trend = "Bullish" if volatility > 0.05 else "Bearish" if volatility < -0.05 else "Stable"
        
        return {
            "source": "Mathematical Fallback",
            "crop": crop,
            "location": location,
            "mandi": "Regional Avg",
            "live_modal_price": round(live_price, 2),
            "trend": trend,
            "volatility_pct": round(volatility * 100, 2),
            "raw_data": None
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

