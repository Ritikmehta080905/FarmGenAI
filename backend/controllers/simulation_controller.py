from ..services.negotiation_service import start_negotiation
from simulation.scenario_runner import run_all as _run_all_scenarios
from negotiation_engine.scoring import calculate_scenario_score


def run_simulation_controller(payload: dict):
    if payload.get("scenario") == "all":
        # Generate and score multiple scenarios
        user_id = payload.get("user_id")
        scenario_keys = ["direct-sale", "storage", "processing"]
        results = []
        
        # Use provided data if available, otherwise fallback to defaults
        base_payload = {
            "user_id": user_id,
            "farmer_name": payload.get("farmer_name") or payload.get("name") or "Farmer",
            "crop": payload.get("crop"),
            "quantity": payload.get("quantity"),
            "min_price": payload.get("min_price"),
            "location": payload.get("location"),
            "quality": payload.get("quality", "A"),
            "language": payload.get("language", "English")
        }

        for skey in scenario_keys:
            if base_payload["crop"]:
                scenario_payload = {**base_payload, "scenario_type": skey}
            else:
                scenario_payload = _get_scenario_payload(skey, user_id)
            
            # Run simulation
            res = start_negotiation(scenario_payload, scenario=scenario_payload.get("scenario_type", "direct-sale"))
            # Score it
            score_data = calculate_scenario_score({
                "status": res.get("status"),
                "scenario_type": skey,
                "final_price": res.get("final_price"),
                "min_price": scenario_payload.get("min_price"),
                "target_price": scenario_payload.get("target_price"),
                "shelf_life": scenario_payload.get("shelf_life")
            })
            res["score"] = score_data["score"]
            res["score_breakdown"] = score_data["breakdown"]
            res["scenario_type"] = skey
            results.append(res)
            
        best_scenario = max(results, key=lambda x: x["score"])["scenario_type"] if results else None
        from llm.llm_client import client as llm_client
        explanation = llm_client.explain_scenarios(results, best_scenario)
        
        return {
            "scenarios": results,
            "best_scenario": best_scenario,
            "explanation": explanation
        }

    scenario = payload["scenario"]
    user_id = payload.get("user_id")
    
    selected = _get_scenario_payload(scenario, user_id)
    if not selected:
        return {
            "negotiation_id": "invalid",
            "status": "invalid_scenario",
            "offers": [],
            "summary": "Scenario not found",
            "final_price": None,
            "next_action": None
        }

    result = start_negotiation(selected, scenario=selected.get("scenario_type", "direct-sale"))
    
    # Score the singular result too
    score_data = calculate_scenario_score({
        "status": result.get("status"),
        "scenario_type": scenario,
        "final_price": result.get("final_price"),
        "min_price": selected.get("min_price"),
        "target_price": selected.get("target_price"),
        "shelf_life": selected.get("shelf_life")
    })
    result["score"] = score_data["score"]
    result["score_breakdown"] = score_data["breakdown"]
    
    return result


def _get_scenario_payload(scenario: str, user_id: str = None):
    scenarios = {
        "direct-sale": {
            "user_id": user_id,
            "farmer_name": "Ramesh",
            "crop": "Tomato",
            "quantity": 1000,
            "min_price": 18,
            "target_price": 25,
            "shelf_life": 4,
            "location": "Nashik",
            "quality": "A",
            "language": "Marathi",
            "scenario_type": "direct-sale"
        },
        "storage": {
            "user_id": user_id,
            "farmer_name": "Suresh",
            "crop": "Onion",
            "quantity": 1200,
            "min_price": 22,
            "target_price": 30,
            "shelf_life": 5,
            "location": "Nashik",
            "quality": "A",
            "language": "Marathi",
            "scenario_type": "storage"
        },
        "processing": {
            "user_id": user_id,
            "farmer_name": "Mahesh",
            "crop": "Tomato",
            "quantity": 800,
            "min_price": 16,
            "target_price": 22,
            "shelf_life": 1,
            "location": "Pune",
            "quality": "B",
            "language": "Hindi",
            "scenario_type": "processing"
        }
    }
    # Backward compatibility
    scenarios["processor"] = scenarios["processing"]
    return scenarios.get(scenario)