from agents.base_agent import BaseAgent


class ProcessorAgent(BaseAgent):

    def __init__(
        self,
        name,
        crop_type,
        processing_capacity,
        processing_cost_per_kg,
        target_price,
        max_price
    ):
        super().__init__(name, "processor")
        self.crop_type = crop_type
        self.processing_capacity = processing_capacity
        self.processing_cost_per_kg = processing_cost_per_kg
        self.target_price = target_price
        self.max_price = max_price
        self.inventory = 0

    def respond_to_offer(self, offer, context=None):
        price = float(offer.get("price", 0))
        quantity = float(offer.get("quantity", 0))
        crop = offer.get("crop", self.crop_type)

        # ── Autonomous Thinking Phase ────────────────────────
        thought = self.think(
            f"You are {self.name}, an Industrial Processor. Request to buy {quantity}kg of {crop} at ₹{price}/kg. "
            f"Target Price: ₹{self.target_price}/kg, Max Price: ₹{self.max_price}/kg. "
            "Analyze if this raw produce purchase is viable for high-value conversion.",
            schema={"decision": "ACCEPT", "reason": "...", "margin_impact": "positive"}
        )

        decision = thought.get("decision", "ACCEPT").upper()
        reason = thought.get("reason", "Processing requested.")

        if crop != self.crop_type:
            decision = "REJECT"
            reason = f"Specialized machinery in this node only supports {self.crop_type} processing."

        if price > self.max_price:
            decision = "REJECT"
            reason = "Price exceeds industrial processing feasibility threshold."

        if decision == "REJECT":
            return {
                "type": "REJECT",
                "message": self.log_action(f"REJECTED processing: {reason}")
            }

        # ── Execution Phase ──────────────────────────────────
        purchase_quantity = min(quantity, self.processing_capacity)
        self.inventory += purchase_quantity

        return {
            "type": "ACCEPT_PROCESSING",
            "price": price,
            "quantity": purchase_quantity,
            "message": self.log_action(f"ACCEPTED for conversion ({purchase_quantity}kg): {reason}")
        }

    def process_inventory(self, quantity):
        if quantity > self.inventory:
            return {"type": "ERROR", "message": self.log_action("Not enough inventory.")}
        self.inventory -= quantity
        processed_output = round(quantity * 0.9, 2)
        return {
            "type": "PROCESS_COMPLETE",
            "input_quantity": quantity,
            "output_quantity": processed_output,
            "message": self.log_action(f"Processed into {processed_output}kg value-added product.")
        }

    def get_status(self):
        return {
            "name": self.name,
            "crop_type": self.crop_type,
            "processing_capacity": self.processing_capacity,
            "inventory": self.inventory,
            "target_price": self.target_price
        }