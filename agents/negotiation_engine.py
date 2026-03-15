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

            print("Farmer chooses to store in warehouse.")
            return

        elif decision == "Sell to processor":
            print("Farmer chooses to sell to processor.")
            return

        elif decision == "Counter offer":
            if new_price:
                farmer_ask = new_price
                print("Farmer sets new ask to:", farmer_ask)
            else:
                # Assume minimum price
                farmer_ask = 18
                print("Farmer counters with minimum price:", farmer_ask)

        # Buyer's turn
        result = buyer.respond(farmer_ask)

        decision = result['decision']
        new_price = result['new_price']
        reason = result['reason']

        print(f"\nBuyer decision: {decision}")
        if new_price:
            print(f"New Price: ₹{new_price}")
        print(f"Reason: {reason}")

        if decision == "Accept offer":
            print("Deal accepted at price:", farmer_ask)
            return

        elif decision == "Reject offer":
            print("Buyer rejects the offer.")
            return

        elif decision == "Counter offer":
            if new_price:
                buyer_offer = new_price
                print("Buyer sets new offer to:", buyer_offer)
            else:
                # Assume higher offer
                buyer_offer += 1
                print("Buyer increases offer to:", buyer_offer)

    print("\nNegotiation ended.")