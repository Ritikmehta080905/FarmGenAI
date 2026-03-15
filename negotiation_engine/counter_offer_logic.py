class CounterOfferLogic:

    """
    Handles counter-offer generation to ensure negotiation converges
    instead of deadlocking.
    """

    def process_counter_offer(self, response):

        price = response.get("price")
        quantity = response.get("quantity")
        agent = response.get("agent", "Unknown")

        # fallback safety
        if price is None:
            price = 0

        # Farmer counter strategy
        if "Farmer" in agent:

            buyer_price = response.get("previous_price", price)

            # move 25% toward buyer price
            new_price = price - (price - buyer_price) * 0.25

            return {
                "type": "COUNTER",
                "price": round(new_price, 2),
                "quantity": quantity,
                "message": f"FarmerAgent: Counter ₹{round(new_price,2)}/kg"
            }

        # Buyer counter strategy
        if "Buyer" in agent:

            farmer_price = response.get("previous_price", price)

            # move 25% toward farmer price
            new_price = price + (farmer_price - price) * 0.25

            return {
                "type": "COUNTER",
                "price": round(new_price, 2),
                "quantity": quantity,
                "message": f"BuyerAgent: Counter ₹{round(new_price,2)}/kg"
            }

        # Default fallback
        return response