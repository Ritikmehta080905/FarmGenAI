"""
Legacy negotiation engine shim — kept for backward compatibility.
All new code should use negotiation_engine.negotiation_manager directly.
"""

from agents.farmer_agent import FarmerAgent
from agents.buyer_agent import BuyerAgent
from negotiation_engine.negotiation_manager import NegotiationManager


def simulate_negotiation(
    crop="Tomato",
    quantity=500,
    min_price=18,
    target_price=16,
    budget=12000,
    max_rounds=5,
):
    """Run a simple agent negotiation and print the outcome."""

    farmer = FarmerAgent(
        name="DemoFarmer",
        crop=crop,
        quantity=quantity,
        min_price=min_price,
        shelf_life=4,
    )

    buyer = BuyerAgent(
        name="DemoBuyer",
        budget=budget,
        max_quantity=quantity + 200,
        target_price=target_price,
    )

    manager = NegotiationManager(farmer=farmer, buyer=buyer, max_rounds=max_rounds)

    import random
    market_price = random.randint(14, 20)

    print(f"\n⚡ Starting negotiation for {quantity}kg {crop}")
    print(f"   Farmer min: ₹{min_price}  |  Buyer target: ₹{target_price}  |  Market: ₹{market_price}")

    result = manager.start_negotiation(market_price)

    state = result.get("state", "UNKNOWN")
    if state == "DEAL":
        price = result["deal"]["price"]
        print(f"\n✅ Deal reached at ₹{price}/kg")
    else:
        print(f"\n❌ Negotiation ended: {state} — {result.get('summary', '')}")

    for log_line in result.get("logs", []):
        print(" ", log_line)

    return result


if __name__ == "__main__":
    simulate_negotiation()