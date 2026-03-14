from agents.farmer_agent import FarmerAgent
from agents.buyer_agent import BuyerAgent


def simulate_negotiation():

    farmer = FarmerAgent(min_price=18, spoilage_days=3)
    buyer = BuyerAgent(max_price=20, spoilage_days=3)

    farmer_ask = 20  # Initial farmer ask
    buyer_offer = 16

    print("Farmer initial ask:", farmer_ask)
    print("Buyer initial offer:", buyer_offer)

    for round in range(3):

        # Farmer's turn
        result = farmer.respond(buyer_offer)

        decision = result['decision']
        new_price = result['new_price']
        reason = result['reason']

        print(f"\nFarmer decision: {decision}")
        if new_price:
            print(f"New Price: ₹{new_price}")
        print(f"Reason: {reason}")

        if decision == "Accept offer":
            print("Deal accepted at price:", buyer_offer)
            return

        elif decision == "Store in warehouse":
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