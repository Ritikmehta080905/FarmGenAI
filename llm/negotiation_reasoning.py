"""
llm/negotiation_reasoning.py

Named decision functions used by tests and legacy scripts.
All functions return a dict: {"decision": str, "new_price": float|None, "reason": str}

Decisions map to human-readable strings for backward-compat:
  "Accept offer" | "Counter offer" | "Reject offer" |
  "Store in warehouse" | "Sell to processor" | "Buy produce"
"""

from llm.llm_client import client as _llm


def _call(role, offered_price, target_price, quantity, market_price=None):
    mp = market_price or offered_price
    raw = _llm.negotiation_reasoning(
        role=role,
        offered_price=offered_price,
        target_price=target_price,
        market_price=mp,
        quantity=quantity,
    )
    decision_map = {
        "ACCEPT":  "Accept offer",
        "COUNTER": "Counter offer",
        "REJECT":  "Reject offer",
    }
    decision = decision_map.get(raw.get("decision", "COUNTER"), "Counter offer")
    return {
        "decision":  decision,
        "new_price": raw.get("counter_price"),
        "reason":    raw.get("reason", ""),
    }


def farmer_decision(min_price: float, buyer_offer: float, spoilage_days: int,
                    quantity: float = 500) -> dict:
    """
    Farmer decides whether to accept, counter, store, or escalate.
    High spoilage urgency can override to warehouse/processor route.
    """
    if spoilage_days <= 2:
        if buyer_offer >= min_price * 0.85:
            return {"decision": "Accept offer",  "new_price": None,
                    "reason": "Critical spoilage; accepting near-min price"}
        return {"decision": "Sell to processor", "new_price": None,
                "reason": "Critical spoilage; moving to processor"}

    result = _call("Farmer", buyer_offer, min_price, quantity)
    if result["decision"] == "Reject offer" and spoilage_days <= 4:
        result["decision"] = "Store in warehouse"
    return result


def buyer_decision(max_price: float, farmer_ask: float, spoilage_days: int,
                   quantity: float = 500) -> dict:
    """Buyer decides whether to accept the farmer's ask price."""
    return _call("Buyer", farmer_ask, max_price, quantity)


def processor_decision(demand_price: float, offered_price: float,
                       quantity: float, spoilage_days: int) -> dict:
    """Processor decides whether to buy produce for processing."""
    if offered_price <= demand_price:
        return {"decision": "Buy produce", "new_price": None,
                "reason": "Offered price within processing budget"}
    # offered_price > demand_price — over budget; counter or reject
    counter = round(demand_price * 1.05, 2)
    return {"decision": "Counter offer", "new_price": counter,
            "reason": f"Offered price exceeds processing budget; counter at {counter}"}


def warehouse_decision(storage_cost_per_day: float, spoilage_days: int,
                       market_price: float) -> dict:
    """Warehouse decides whether to store or recommend fast sale."""
    total_cost = storage_cost_per_day * spoilage_days
    if spoilage_days <= 2 or total_cost >= market_price * 0.3:
        return {"decision": "Reject offer",
                "new_price": None,
                "reason": "Storage cost too high given spoilage window; sell fast"}
    return {"decision": "Accept offer",
            "new_price": None,
            "reason": f"Storage viable; cost ₹{total_cost:.2f} over {spoilage_days} days"}
