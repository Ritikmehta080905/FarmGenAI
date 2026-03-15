import random

from agents.farmer_agent import FarmerAgent
from agents.buyer_agent import BuyerAgent
from agents.warehouse_agent import WarehouseAgent
from negotiation_engine.negotiation_manager import NegotiationManager

from shared.event_bus import event_bus

# ---------------------------------------------------------------------------
# Scenario definitions
# price_gap controls how far above market_price the farmer asks.
# A small gap (<=4) usually converges to a DEAL within max_rounds.
# A large gap (>=12) almost never converges, triggering warehouse escalation.
# ---------------------------------------------------------------------------
_SCENARIO_DEFS = {
    "direct_sale": {
        "scenario": "Direct Sale Scenario",
        "scenario_type": "direct-sale",
        "crop": "Tomato",
        "quantity": 500,
        "max_rounds": 6,
        "price_gap": 3,
    },
    "storage": {
        "scenario": "Storage Fallback Scenario",
        "scenario_type": "storage",
        "crop": "Wheat",
        "quantity": 800,
        "max_rounds": 4,
        "price_gap": 14,
    },
    "processing": {
        "scenario": "Processing Route Scenario",
        "scenario_type": "processing",
        "crop": "Sugarcane",
        "quantity": 1000,
        "max_rounds": 5,
        "price_gap": 4,
    },
}


def run_all(scenario_name="all"):
    """Run one or all simulation scenarios.

    Args:
        scenario_name: 'all' | 'direct_sale' | 'storage' | 'processing'

    Returns:
        dict with keys: scenarios, metrics, results
    """

    if scenario_name == "all":
        to_run = list(_SCENARIO_DEFS.values())
    else:
        to_run = [_SCENARIO_DEFS.get(scenario_name, _SCENARIO_DEFS["direct_sale"])]

    scenarios = []
    for s in to_run:
        result = run_scenario(s)
        scenarios.append(result)

    # Build metrics — guard against missing 'deal' key (FAILED state)
    deal_prices = []
    for s in scenarios:
        deal = s["result"].get("deal")
        if deal and isinstance(deal, dict):
            price = deal.get("price") or deal.get("storage_cost")
            if price is not None:
                deal_prices.append(float(price))

    total = len(scenarios)
    success_count = sum(1 for s in scenarios if s["result"].get("state") == "DEAL")
    success_rate = round((success_count / total) * 100, 1) if total else 0
    avg_price = round(sum(deal_prices) / len(deal_prices), 2) if deal_prices else 0

    records = []
    for s in scenarios:
        deal = s["result"].get("deal") or {}
        records.append({
            "scenario": s["scenario"],
            "scenario_type": s.get("scenario_type", ""),
            "status": s["result"].get("state", "UNKNOWN"),
            "final_price": deal.get("price"),
            "quantity": s["market_tick"].get("quantity"),
            "summary": s["result"].get("summary", ""),
            "offers": s.get("logs", []),
            "price_series": s.get("price_series", []),
        })

    metrics = {
        "total_scenarios": total,
        "successful_outcomes": success_count,
        "success_rate": success_rate,
        "average_final_price": avg_price,
        "records": records,
    }

    return {
        "scenarios": scenarios,
        "metrics": metrics,
        "results": records,
    }


def run_scenario(scenario):

    market_price = random.randint(14, 20)

    market_tick = {
        "market_price": market_price,
        "demand": "low",
        "supply": "high",
        "active_buyers": 1,
        "quantity": scenario["quantity"],
    }

    event_bus.emit("market_tick", market_tick)

    price_gap = scenario.get("price_gap", 4)

    farmer = FarmerAgent(
        name="SimFarmer",
        crop=scenario["crop"],
        quantity=scenario["quantity"],
        min_price=market_price + price_gap,
        shelf_life=5,
    )

    buyer = BuyerAgent(
        name="SimBuyer",
        budget=random.randint(8000, 12000),
        max_quantity=scenario["quantity"] + 200,
        target_price=market_price,
    )

    warehouse = WarehouseAgent(
        name="SimWarehouse",
        capacity=5000,
        storage_cost_per_kg=1.5,
        location="Nashik",
    )

    manager = NegotiationManager(
        farmer=farmer,
        buyer=buyer,
        warehouse=warehouse,
        max_rounds=scenario["max_rounds"],
    )

    result = manager.start_negotiation(market_price)

    return {
        "scenario": scenario["scenario"],
        "scenario_type": scenario.get("scenario_type", ""),
        "market_tick": market_tick,
        "result": result,
        "logs": manager.logs,
        "price_series": manager.memory.get_price_series(),
    }