from agents.base_agent import BaseAgent


class CompostAgent(BaseAgent):
    def __init__(self, name, base_price=7.5):
        super().__init__(name, "compost")
        self.base_price = base_price

    def respond_to_offer(self, offer, context=None):
        price = float(offer.get("price", self.base_price))
        quantity = float(offer.get("quantity", 0))
        crop = offer.get("crop", "Organic waste")

        # ── Autonomous Thinking Phase ────────────────────────
        thought = self.think(
            f"You are {self.name}, a Compost & Waste Recovery Agent. Request to take {quantity}kg of {crop} at ₹{price}/kg. "
            f"Base Valuation: ₹{self.base_price}/kg. "
            "Analyze if this material is suitable for regenerative farming or bio-recovery.",
            schema={"decision": "ACCEPT", "reason": "...", "priority": "normal"}
        )

        decision = thought.get("decision", "ACCEPT").upper()
        reason = thought.get("reason", "Waste disposal requested.")

        if price > self.base_price * 1.5:
             # Even compost has limits on how much it can pay for waste
             decision = "REJECT"
             reason = "Requested price exceeds bio-recovery value of organic material."

        if decision == "REJECT":
            return {
                "type": "REJECT",
                "message": self.log_action(f"REJECTED compost: {reason}")
            }

        # ── Execution Phase ──────────────────────────────────
        return {
            "type": "ACCEPT_COMPOST",
            "price": price,
            "quantity": quantity,
            "message": self.log_action(f"ACCEPTED for eco-recovery ({quantity}kg): {reason}")
        }

    def get_status(self):
        return {
            "name": self.name,
            "base_price": self.base_price
        }
