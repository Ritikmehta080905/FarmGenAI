import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.farmer_agent import FarmerAgent
from agents.buyer_agent import BuyerAgent
from negotiation_engine.negotiation_manager import NegotiationManager


def run_test():

    farmer = FarmerAgent(
        name="FarmerAgent",
        crop="Tomato",
        quantity=1000,
        min_price=18,
        shelf_life=4
    )

    buyer = BuyerAgent(
        name="BuyerAgent",
        budget=20000,
        max_quantity=600,
        target_price=18
    )

    manager = NegotiationManager(farmer, buyer)

    result = manager.start_negotiation()

    print("\n--- Negotiation Conversation ---\n")

    for entry in manager.log:
        print(entry)

    if result:
        print("\nDeal Completed!")
    else:
        print("\nNo Deal Reached.")


if __name__ == "__main__":
    run_test()