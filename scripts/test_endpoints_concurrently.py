import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000"

async def test_endpoint(client, url, method="GET", payload=None):
    try:
        if method == "GET":
            response = await client.get(f"{BASE_URL}{url}")
        else:
            response = await client.post(f"{BASE_URL}{url}", json=payload)
        return response.status_code
    except Exception as e:
        return str(e)

async def main():
    async with httpx.AsyncClient() as client:
        # Start API backend in a separate terminal before running this script
        
        # Endpoints to hit
        endpoints = [
            ("/api/v1/buyers/", "GET", None),
            ("/api/v1/farmers/", "GET", None),
            ("/api/v1/warehouse/", "GET", None),
            ("/api/v1/dashboards/platform", "GET", None),
        ]
        
        tasks = []
        for _ in range(20): # Concurrent requests
            for url, method, payload in endpoints:
                tasks.append(test_endpoint(client, url, method, payload))
                
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        print(f"Executed {len(tasks)} concurrent requests in {end_time - start_time:.2f} seconds.")
        
        status_counts = {}
        for r in results:
            status_counts[r] = status_counts.get(r, 0) + 1
            
        for status, count in status_counts.items():
            print(f"Status {status}: {count} responses")
            
        if status_counts.get(200, 0) == len(tasks):
            print("SUCCESS: All endpoints returned 200 OK!")
        else:
            print("FAILURE: Some endpoints failed.")

if __name__ == "__main__":
    asyncio.run(main())
