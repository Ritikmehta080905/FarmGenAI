import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    from backend.services.negotiation_service import start_negotiation
    payload = {
        "crop": "Tomato",
        "quantity": 1000,
        "min_price": 18,
        "farmer_name": "Test",
        "shelf_life": 4,
        "location": "Nashik",
        "quality": "A",
        "language": "English",
        "max_rounds": 3,
    }
    try:
        result = await start_negotiation(payload)
        print("SUCCESS:", list(result.keys()))
        print("status:", result.get("status"))
        print("final_price:", result.get("final_price"))
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test())
