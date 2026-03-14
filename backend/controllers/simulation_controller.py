from backend.services.negotiation_service import start_negotiation


def run_simulation_controller(payload: dict):
    scenario = payload["scenario"]
    user_id = payload.get("user_id")

    scenarios = {
        "direct-sale": {
            "user_id": user_id,
            "farmer_name": "Ramesh",
            "crop": "Tomato",
            "quantity": 1000,
            "min_price": 18,
            "shelf_life": 4,
            "location": "Nashik",
            "quality": "A",
            "language": "Marathi"
        },
        "storage": {
            "user_id": user_id,
            "farmer_name": "Suresh",
            "crop": "Onion",
            "quantity": 1200,
            "min_price": 22,
            "shelf_life": 5,
            "location": "Nashik",
            "quality": "A",
            "language": "Marathi"
        },
        "processor": {
            "user_id": user_id,
            "farmer_name": "Mahesh",
            "crop": "Tomato",
            "quantity": 800,
            "min_price": 16,
            "shelf_life": 1,
            "location": "Pune",
            "quality": "B",
            "language": "Hindi"
        }
    }

    if scenario not in scenarios:
        return {
            "negotiation_id": "invalid",
            "status": "invalid_scenario",
            "offers": [],
            "summary": "Scenario not found",
            "final_price": None,
            "next_action": None
        }

    result = start_negotiation(scenarios[scenario])
    return result