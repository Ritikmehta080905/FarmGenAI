from agents.base_agent import BaseAgent


class WarehouseAgent(BaseAgent):

    def __init__(
        self,
        name,
        capacity,
        storage_cost_per_kg,
        location=None
    ):

        super().__init__(name, "warehouse")

        # Warehouse capacity
        self.capacity = capacity

        # Current stored produce
        self.current_inventory = 0

        # Storage pricing
        self.storage_cost_per_kg = storage_cost_per_kg

        # Storage records
        self.storage_records = []

        self.location = location

    # ------------------------------------------------
    # Check available capacity
    # ------------------------------------------------

    def available_capacity(self):

        return self.capacity - self.current_inventory

    # ------------------------------------------------
    # Storage offer to farmer
    # ------------------------------------------------

    def make_offer(self, context=None):

        message = self.log_action(
            f"Storage available. Cost ₹{self.storage_cost_per_kg}/kg"
        )

        return {
            "type": "OFFER_STORAGE",
            "price": self.storage_cost_per_kg,
            "message": message
        }

    # ------------------------------------------------
    # Evaluate storage request
    # ------------------------------------------------

    def evaluate_request(self, quantity):

        if quantity > self.available_capacity():
            return "no_capacity"

        return "acceptable"

    # ------------------------------------------------
    # Respond to farmer storage request
    # ------------------------------------------------

    def respond_to_offer(self, offer, context=None):

        quantity = offer["quantity"]

        evaluation = self.evaluate_request(quantity)

        # ------------------------
        # Warehouse full
        # ------------------------

        if evaluation == "no_capacity":

            return {
                "type": "REJECT",
                "message": self.log_action(
                    "Warehouse full. Cannot store produce."
                )
            }

        # ------------------------
        # Accept storage
        # ------------------------

        self.current_inventory += quantity

        storage_cost = quantity * self.storage_cost_per_kg

        record = {
            "crop": offer.get("crop", "unknown"),
            "quantity": quantity,
            "cost": storage_cost
        }

        self.storage_records.append(record)

        return {
            "type": "ACCEPT_STORAGE",
            "quantity": quantity,
            "cost": storage_cost,
            "message": self.log_action(
                f"Accepted {quantity}kg for storage. Cost ₹{storage_cost}"
            )
        }

    # ------------------------------------------------
    # Release produce from warehouse
    # ------------------------------------------------

    def release_stock(self, quantity):

        if quantity > self.current_inventory:

            return {
                "type": "REJECT",
                "message": self.log_action(
                    "Not enough stock in warehouse."
                )
            }

        self.current_inventory -= quantity

        return {
            "type": "RELEASE",
            "quantity": quantity,
            "message": self.log_action(
                f"Released {quantity}kg from storage."
            )
        }

    # ------------------------------------------------
    # Warehouse status
    # ------------------------------------------------

    def get_status(self):

        return {
            "capacity": self.capacity,
            "current_inventory": self.current_inventory,
            "available_capacity": self.available_capacity(),
            "storage_cost_per_kg": self.storage_cost_per_kg,
            "location": self.location
        }