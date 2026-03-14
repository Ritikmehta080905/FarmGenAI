import random
from agents.base_agent import BaseAgent


class BuyerAgent(BaseAgent):

    def __init__(
        self,
        name,
        budget,
        max_quantity,
        target_price,
        location=None
    ):

        super().__init__(name, "buyer")

        # Financial constraint
        self.budget = budget

        # Maximum quantity buyer can purchase
        self.max_quantity = max_quantity

        # Target price buyer prefers
        self.target_price = target_price

        # Current inventory
        self.inventory = 0

        # Location
        self.location = location

    # ------------------------------------------------
    # Buyer initial offer
    # ------------------------------------------------

    def make_offer(self, context=None):

        offer_price = max(1, self.target_price - random.randint(1, 3))

        quantity = min(self.max_quantity, random.randint(100, 500))

        message = self.log_action(
            f"I offer ₹{offer_price}/kg for {quantity}kg"
        )

        return {
            "price": offer_price,
            "quantity": quantity,
            "message": message
        }

    # ------------------------------------------------
    # Offer evaluation
    # ------------------------------------------------

    def evaluate_offer(self, price, quantity):

        total_cost = price * quantity

        # Cannot afford
        if total_cost > self.budget:
            return "too_expensive"

        # Too much quantity
        if quantity > self.max_quantity:
            return "too_large"

        # Good deal
        if price <= self.target_price:
            return "excellent"

        # Slightly above target
        if price <= self.target_price + 2:
            return "acceptable"

        return "bad"

    # ------------------------------------------------
    # Negotiation response
    # ------------------------------------------------

    def respond_to_offer(self, offer, context=None):

        price = offer["price"]
        quantity = offer["quantity"]

        evaluation = self.evaluate_offer(price, quantity)

        # -----------------------
        # Excellent deal
        # -----------------------

        if evaluation == "excellent":

            purchasable_qty = min(
                quantity,
                self.max_quantity,
                self.budget // price
            )

            self.inventory += purchasable_qty
            self.budget -= purchasable_qty * price

            return {
                "type": "ACCEPT",
                "price": price,
                "quantity": purchasable_qty,
                "message": self.log_action(
                    f"Accepted {purchasable_qty}kg at ₹{price}/kg"
                )
            }

        # -----------------------
        # Acceptable deal
        # -----------------------

        if evaluation == "acceptable":

            counter_price = max(
                self.target_price,
                price - random.randint(1, 2)
            )

            return {
                "type": "COUNTER",
                "price": counter_price,
                "quantity": quantity,
                "message": self.log_action(
                    f"Counter offer ₹{counter_price}/kg for {quantity}kg"
                )
            }

        # -----------------------
        # Quantity too large
        # -----------------------

        if evaluation == "too_large":

            reduced_quantity = self.max_quantity

            return {
                "type": "COUNTER",
                "price": price,
                "quantity": reduced_quantity,
                "message": self.log_action(
                    f"I can only purchase {reduced_quantity}kg"
                )
            }

        # -----------------------
        # Cannot afford
        # -----------------------

        if evaluation == "too_expensive":

            affordable_qty = self.budget // price

            if affordable_qty > 0:

                return {
                    "type": "COUNTER",
                    "price": price,
                    "quantity": affordable_qty,
                    "message": self.log_action(
                        f"I can afford only {affordable_qty}kg"
                    )
                }

            return {
                "type": "REJECT",
                "message": self.log_action(
                    "Cannot afford this offer."
                )
            }

        # -----------------------
        # Bad deal
        # -----------------------

        if evaluation == "bad":

            counter_price = max(
                1,
                self.target_price - random.randint(1, 3)
            )

            counter_quantity = min(
                quantity,
                self.max_quantity
            )

            return {
                "type": "COUNTER",
                "price": counter_price,
                "quantity": counter_quantity,
                "message": self.log_action(
                    f"Offer too high. Countering ₹{counter_price}/kg"
                )
            }

    # ------------------------------------------------
    # Buyer status
    # ------------------------------------------------

    def get_buyer_info(self):

        return {
            "budget_remaining": self.budget,
            "inventory": self.inventory,
            "max_quantity": self.max_quantity,
            "target_price": self.target_price,
            "location": self.location
        }