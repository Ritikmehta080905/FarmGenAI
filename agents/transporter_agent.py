from agents.base_agent import BaseAgent


class TransportAgent(BaseAgent):

    def __init__(
        self,
        name,
        vehicle_capacity,
        cost_per_km_per_kg,
        base_fee,
        speed_kmph=40
    ):

        super().__init__(name, "transport")

        self.vehicle_capacity = vehicle_capacity
        self.cost_per_km_per_kg = cost_per_km_per_kg
        self.base_fee = base_fee
        self.speed_kmph = speed_kmph

        self.active_deliveries = []

    def evaluate_offer(self, offer, context=None):
        quantity = offer.get("quantity", 0)
        return "ACCEPT" if self.can_transport(quantity) else "REJECT"

    # ---------------------------------------------
    # Calculate transport cost
    # ---------------------------------------------

    def calculate_transport_cost(self, quantity, distance):

        cost = (
            quantity
            * distance
            * self.cost_per_km_per_kg
        ) + self.base_fee

        return round(cost, 2)

    # ---------------------------------------------
    # Estimate delivery time
    # ---------------------------------------------

    def estimate_delivery_time(self, distance):

        time = distance / self.speed_kmph

        return round(time, 2)

    # ---------------------------------------------
    # Check capacity
    # ---------------------------------------------

    def can_transport(self, quantity):

        return quantity <= self.vehicle_capacity

    # ---------------------------------------------
    # Make transport offer
    # ---------------------------------------------

    def make_offer(self, context):

        quantity = context["quantity"]
        distance = context["distance"]

        if not self.can_transport(quantity):

            return {
                "type": "REJECT",
                "message": self.log_action(
                    "Cannot transport. Load exceeds vehicle capacity."
                )
            }

        cost = self.calculate_transport_cost(quantity, distance)

        delivery_time = self.estimate_delivery_time(distance)

        return {
            "type": "TRANSPORT_OFFER",
            "quantity": quantity,
            "cost": cost,
            "delivery_time": delivery_time,
            "message": self.log_action(
                f"Transport offer: {quantity}kg over {distance}km. Cost ₹{cost}. ETA {delivery_time} hours."
            )
        }

    # ---------------------------------------------
    # Respond to transport request
    # ---------------------------------------------

    def respond_to_offer(self, offer, context=None):

        quantity = offer["quantity"]
        distance = offer["distance"]

        if not self.can_transport(quantity):

            return {
                "type": "REJECT",
                "message": self.log_action(
                    "Transport rejected due to capacity limit."
                )
            }

        cost = self.calculate_transport_cost(quantity, distance)

        delivery_time = self.estimate_delivery_time(distance)

        delivery = {
            "quantity": quantity,
            "distance": distance,
            "cost": cost,
            "delivery_time": delivery_time
        }

        self.active_deliveries.append(delivery)

        return {
            "type": "ACCEPT_TRANSPORT",
            "quantity": quantity,
            "cost": cost,
            "delivery_time": delivery_time,
            "message": self.log_action(
                f"Accepted transport of {quantity}kg over {distance}km. Cost ₹{cost}"
            )
        }

    # ---------------------------------------------
    # Complete delivery
    # ---------------------------------------------

    def complete_delivery(self, delivery_index):

        if delivery_index >= len(self.active_deliveries):

            return {
                "type": "ERROR",
                "message": self.log_action(
                    "Invalid delivery index."
                )
            }

        delivery = self.active_deliveries.pop(delivery_index)

        return {
            "type": "DELIVERY_COMPLETE",
            "details": delivery,
            "message": self.log_action(
                f"Delivery completed: {delivery['quantity']}kg transported."
            )
        }

    # ---------------------------------------------
    # Transport status
    # ---------------------------------------------

    def get_status(self):

        return {
            "vehicle_capacity": self.vehicle_capacity,
            "active_deliveries": len(self.active_deliveries),
            "cost_per_km_per_kg": self.cost_per_km_per_kg
        }


class TransporterAgent(TransportAgent):
    pass