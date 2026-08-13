import json
import logging
import random
from typing import Dict, Any, Optional
import urllib.request
import urllib.parse
import urllib.error

logger = logging.getLogger("backend.services.external_apis")

class OpenMeteoClient:
    """
    Client for fetching real-time weather data from the open-meteo API.
    Does not require an API key.
    """
    @staticmethod
    async def get_weather(location: str) -> Optional[Dict[str, Any]]:
        import asyncio
        loop = asyncio.get_event_loop()
        
        def _fetch():
            try:
                # 1. Geocoding: Get lat/lon for the location
                safe_location = urllib.parse.quote(location)
                geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={safe_location}&count=1"
                
                req = urllib.request.Request(geo_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    geo_data = json.loads(response.read().decode())
                    
                if not geo_data.get("results"):
                    logger.warning(f"No geocoding results found for {location}")
                    return None
                    
                lat = geo_data["results"][0]["latitude"]
                lon = geo_data["results"][0]["longitude"]
                
                # 2. Fetch weather forecast
                weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,wind_speed_10m"
                req2 = urllib.request.Request(weather_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req2, timeout=5) as w_response:
                    weather_data = json.loads(w_response.read().decode())
                    
                current = weather_data.get("current", {})
                return {
                    "temperature_c": current.get("temperature_2m"),
                    "precipitation_mm": current.get("precipitation"),
                    "wind_speed_kmh": current.get("wind_speed_10m"),
                    "location_resolved": geo_data["results"][0]["name"]
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
