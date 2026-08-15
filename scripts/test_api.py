import asyncio
from backend.services.external_apis import OSRMClient, OpenMeteoClient

async def test():
    print("Testing OpenMeteo for Nashik...")
    weather = await OpenMeteoClient.get_weather('Nashik')
    print("Weather:", weather)
    
    print("\nTesting OSRM for Nashik -> Pune...")
    dist = await OSRMClient.get_driving_distance_km('Nashik', 'Pune')
    print("Distance:", dist)

if __name__ == "__main__":
    asyncio.run(test())
