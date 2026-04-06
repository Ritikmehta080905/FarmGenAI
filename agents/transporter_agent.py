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

    def calculate_transport_cost(self, quantity, distance):
        cost = (quantity * distance * self.cost_per_km_per_kg) + self.base_fee
        return round(cost, 2)

    def estimate_delivery_time(self, distance):
        time = distance / self.speed_kmph
        return round(time, 2)

    def can_transport(self, quantity):
        return quantity <= self.vehicle_capacity

    def respond_to_offer(self, offer, context=None):
        quantity = float(offer.get("quantity", 0))
        distance = float(offer.get("distance", 50))
        
        # ── Autonomous Thinking Phase ────────────────────────
        thought = self.think(
            f"You are {self.name}, a Transport Agent. Request to move {quantity}kg over {distance}km. "
            f"Vehicle Cap: {self.vehicle_capacity}kg. "
            "Analyze if this route is profitable and viable.",
            schema={"decision": "ACCEPT", "reason": "...", "priority": "high"}
        )

        decision = thought.get("decision", "ACCEPT").upper()
        reason = thought.get("reason", "Route requested.")

        if not self.can_transport(quantity):
            decision = "REJECT"
            reason = "Strict payload limit exceeded for available vehicle."

        if decision == "REJECT":
            return {
                "type": "REJECT",
                "message": self.log_action(f"REJECTED transport: {reason}")
            }

        # ── Execution Phase ──────────────────────────────────
        cost = self.calculate_transport_cost(quantity, distance)
        delivery_time = self.estimate_delivery_time(distance)

        delivery = {
            "quantity": quantity,
            "distance": distance,
            "cost": cost,
            "delivery_time": delivery_time,
            "reason": reason
        }
        self.active_deliveries.append(delivery)

        return {
            "type": "ACCEPT_TRANSPORT",
            "quantity": quantity,
            "cost": cost,
            "delivery_time": delivery_time,
            "message": self.log_action(f"ACCEPTED transport ({distance}km): {reason}")
        }

    def get_status(self):
        return {
            "vehicle_capacity": self.vehicle_capacity,
            "active_deliveries": len(self.active_deliveries),
            "cost_per_km_per_kg": self.cost_per_km_per_kg
        }


class TransporterAgent(TransportAgent):
    """Naming alias for system consistency."""
    pass