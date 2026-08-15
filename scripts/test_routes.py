import asyncio
from fastapi.testclient import TestClient
from backend.main import app
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_routes")

def run_tests():
    logger.info("Initializing TestClient...")
    with TestClient(app) as client:
        # Test 1: Dashboards (dashboard_routes.py)
        logger.info("Testing GET /api/v1/dashboards/platform")
        # Note: Depending on authentication, this might return 401 Unauthorized instead of 500. 
        # But if the auth dependency resolves, it hits the controller. Let's see.
        response = client.get("/api/v1/dashboards/platform")
        logger.info(f"Response status: {response.status_code}")
        if response.status_code == 500:
            logger.error(f"Response text: {response.text}")
            
        # Test 2: Negotiation Agents (negotiation_routes.py)
        logger.info("Testing GET /api/v1/negotiation/agents")
        response = client.get("/api/v1/negotiation/agents")
        logger.info(f"Response status: {response.status_code}")
        if response.status_code == 500:
            logger.error(f"Response text: {response.text}")
            
        # Test 3: Transport Fleet (transport_routes.py)
        logger.info("Testing GET /api/v1/transport/fleet")
        response = client.get("/api/v1/transport/fleet")
        logger.info(f"Response status: {response.status_code}")
        if response.status_code == 500:
            logger.error(f"Response text: {response.text}")

if __name__ == "__main__":
    run_tests()
