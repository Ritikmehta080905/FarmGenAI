"""
negotiation_engine/scoring.py - Scenario Scoring Engine
Calculates scores (0-100) for different supply chain outcomes.
"""

def calculate_scenario_score(scenario_data: dict) -> dict:
    """
    Calculates a multi-dimensional score for a given negotiation outcome.
    
    Args:
        scenario_data (dict): Contains 'final_price', 'min_price', 'target_price', 
                             'status', 'scenario_type', and 'shelf_life'.
    
    Returns:
        dict: Total score and breakdown.
    """
    status = scenario_data.get("status", "FAILED")
    scenario_type = scenario_data.get("scenario_type", "direct-sale")
    final_price = scenario_data.get("final_price", 0)
    min_price = scenario_data.get("min_price", 1)  # avoid division by zero
    target_price = scenario_data.get("target_price", final_price or min_price)

    # 1. Price Satisfaction (40%)
    # For Farmers, a higher final_price is better.
    # For Buyers, a lower final_price is better.
    # Logic: normalize final_price between min_price and target_price.
    if status == "CONTRACT" and final_price:
        if final_price >= min_price:
            # How much better than minimum did we do?
            price_score = min(max(((final_price / min_price) * 100), 0), 100)
        else:
            price_score = 0
    else:
        price_score = 0

    # 2. Waste Reduction (30%)
    # Direct sale = 100, Storage = 70, Processing = 50, Compost = 20, Failed = 0
    waste_map = {
        "direct-sale": 100,
        "storage": 80,
        "processing": 60,
        "compost": 30,
        "failed": 0
    }
    waste_score = waste_map.get(scenario_type if status == "CONTRACT" else "failed", 0)

    # 3. Freshness / Speed (30%)
    # Higher score if the shelf life is high.
    shelf_life = scenario_data.get("shelf_life", 1)
    freshness_score = min(shelf_life * 20, 100) 

    # Weighted Average
    total_score = (price_score * 0.4) + (waste_score * 0.3) + (freshness_score * 0.3)
    
    return {
        "score": round(total_score, 1),
        "breakdown": {
            "price_satisfaction": round(price_score, 1),
            "waste_reduction": round(waste_score, 1),
            "freshness": round(freshness_score, 1)
        }
    }
