import random
from agents.base_agent import BaseAgent


class FarmerAgent(BaseAgent):

    def __init__(
        self,
        name,
        crop,
        quantity,
        min_price,
        shelf_life,
        location=None,
        min_sale_quantity=100
    ):

        super().__init__(name, "farmer")

        # Crop information
        self.crop = crop
        self.quantity = quantity
        self.location = location

        # Price constraints
        self.min_price = min_price
        self.current_price = min_price + random.randint(2, 5)

        # Shelf life (perishability)
        self.shelf_life = shelf_life

        # Quantity constraints
        self.min_sale_quantity = min_sale_quantity

        # fallback options
        self.has_storage_option = True
        self.has_processor_option = True

    # ------------------------------------------------
    # Farmer initial offer
    # ------------------------------------------------

    def make_offer(self, context=None):

        message = self.log_action(
            f"Selling {self.quantity}kg {self.crop} at ₹{self.current_price}/kg"
        )

        return {
            "price": self.current_price,
            "quantity": self.quantity,
            "message": message
        }

    # ------------------------------------------------
    # Evaluate buyer offer
    # ------------------------------------------------

    def evaluate_offer(self, price, quantity):

        if quantity < self.min_sale_quantity:
            return "too_small"

        if price >= self.current_price:
            return "excellent"

        if price >= self.min_price:
            return "acceptable"

        return "bad"

    # ------------------------------------------------
    # Negotiation response
    # ------------------------------------------------

    def respond_to_offer(self, offer, context=None):

        price = offer["price"]
        quantity = offer["quantity"]

        evaluation = self.evaluate_offer(price, quantity)

        # ---------------------------
        # Excellent offer
        # ---------------------------

        if evaluation == "excellent":

            accepted_qty = min(quantity, self.quantity)

            self.quantity -= accepted_qty

            return {
                "type": "ACCEPT",
                "price": price,
                "quantity": accepted_qty,
                "message": self.log_action(
                    f"Accepted {accepted_qty}kg at ₹{price}/kg"
                )
            }

        # ---------------------------
        # Acceptable offer
        # ---------------------------

        if evaluation == "acceptable":

            # perishability pressure
            if self.shelf_life <= 2:

                accepted_qty = min(quantity, self.quantity)

                self.quantity -= accepted_qty

                return {
                    "type": "ACCEPT",
                    "price": price,
                    "quantity": accepted_qty,
                    "message": self.log_action(
                        f"Due to shelf life risk, accepted {accepted_qty}kg at ₹{price}/kg"
                    )
                }

            # counter with slightly higher price
            counter_price = max(
                price + random.randint(1, 2),
                self.min_price
            )

            self.current_price = counter_price

            return {
                "type": "COUNTER",
                "price": counter_price,
                "quantity": quantity,
                "message": self.log_action(
                    f"Counter offer ₹{counter_price}/kg for {quantity}kg"
                )
            }

        # ---------------------------
        # Quantity too small
        # ---------------------------

        if evaluation == "too_small":

            return {
                "type": "COUNTER",
                "price": self.current_price,
                "quantity": self.min_sale_quantity,
                "message": self.log_action(
                    f"Minimum sale quantity is {self.min_sale_quantity}kg"
                )
            }

        # ---------------------------
        # Bad offer
        # ---------------------------

        if evaluation == "bad":

            # spoilage risk
            if self.shelf_life <= 1:

                accepted_qty = min(quantity, self.quantity)

                self.quantity -= accepted_qty

                return {
                    "type": "ACCEPT",
                    "price": price,
                    "quantity": accepted_qty,
                    "message": self.log_action(
                        f"Produce may spoil, accepted {accepted_qty}kg at ₹{price}/kg"
                    )
                }

            # warehouse option
            if self.shelf_life > 3 and self.has_storage_option:

                return {
                    "type": "STORE",
                    "message": self.log_action(
                        "Offer too low. Considering warehouse storage."
                    )
                }

            # processor fallback
            if self.has_processor_option:

                return {
                    "type": "PROCESS",
                    "message": self.log_action(
                        "Buyer price too low. Considering selling to processor."
                    )
                }

            # counter offer fallback
            reduction = random.randint(1, 3)

            counter_price = max(
                self.min_price,
                self.current_price - reduction
            )

            self.current_price = counter_price

            return {
                "type": "COUNTER",
                "price": counter_price,
                "quantity": quantity,
                "message": self.log_action(
                    f"Counter offer ₹{counter_price}/kg"
                )
            }

    # ------------------------------------------------
    # Shelf life simulation
    # ------------------------------------------------

    def reduce_shelf_life(self):

        if self.shelf_life > 0:
            self.shelf_life -= 1

            self.log_action(
                f"Shelf life reduced. Remaining days: {self.shelf_life}"
            )

    # ------------------------------------------------
    # Produce information
    # ------------------------------------------------

    def get_produce_info(self):

        return {
            "crop": self.crop,
            "quantity_remaining": self.quantity,
            "min_price": self.min_price,
            "current_price": self.current_price,
            "shelf_life": self.shelf_life,
            "location": self.location
        }