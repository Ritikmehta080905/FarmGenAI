from agents.buyer_agent import BuyerAgent

class RestaurantAgent(BuyerAgent):
    """
    A specialized buyer agent that represents restaurants or premium grocers.
    They demand high freshness (shelf-life) and buy in smaller quantities,
    but are willing to pay a premium price for quality.
    """

    def __init__(
        self,
        name,
        budget,
        max_quantity,
        target_price,
        min_shelf_life=3,
        premium_ratio=1.1,
        location=None
    ):
        super().__init__(name, budget, max_quantity, target_price, location)
        self.role = "restaurant"
        self.min_shelf_life = min_shelf_life
        self.premium_ratio = premium_ratio

    def make_offer(self, context=None):
        # A restaurant offers near the target price for premium quality
        offer_price = self.target_price
        quantity = min(self.max_quantity, 50)  # usually smaller batches
        message = self.log_action(f"We demand fresh produce. Offering premium ₹{offer_price}/kg for {quantity}kg")
        return {
            "price": offer_price,
            "quantity": quantity,
            "message": message
        }

    def respond_to_offer(self, offer, context=None):
        shelf_life = context.get("shelf_life", 0) if context else 0
        
        # Immediate rejection if produce is too close to spoiling
        if shelf_life > 0 and shelf_life < self.min_shelf_life:
            return {
                "type": "REJECT",
                "price": offer["price"],
                "quantity": offer["quantity"],
                "message": self.log_action(f"REJECTED. Freshness is too low for us (needs at least {self.min_shelf_life} days shelf life).")
            }

        # Be willing to pay premium if criteria are met
        adjusted_target = self.target_price * self.premium_ratio
        
        if offer["price"] <= adjusted_target:
            purchasable_qty = min(offer["quantity"], self.max_quantity, self.budget // offer["price"])
            self.inventory += purchasable_qty
            self.budget -= purchasable_qty * offer["price"]
            return {
                "type": "ACCEPT",
                "price": offer["price"],
                "quantity": purchasable_qty,
                "message": self.log_action(f"ACCEPTED ₹{offer['price']}/kg because quality meets our premium standards.")
            }
        
        # Else, delegate to normal buyer LLM/fallback logic
        return super().respond_to_offer(offer, context)
