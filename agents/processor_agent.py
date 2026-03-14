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

        # Maximum quantity processor can process
        self.processing_capacity = processing_capacity

        # Cost of processing per kg
        self.processing_cost_per_kg = processing_cost_per_kg

        # Preferred purchase price
        self.target_price = target_price

        # Maximum acceptable price
        self.max_price = max_price

        # Current inventory
        self.inventory = 0

    # ---------------------------------------------
    # Make initial offer to farmer
    # ---------------------------------------------

    def make_offer(self, context):

        quantity = context["quantity"]
        crop = context["crop"]

        if crop != self.crop_type:

            return {
                "type": "REJECT",
                "message": self.log_action(
                    f"Cannot process crop type {crop}"
                )
            }

        purchase_quantity = min(quantity, self.processing_capacity)

        return {
            "type": "OFFER",
            "price": self.target_price,
            "quantity": purchase_quantity,
            "message": self.log_action(
                f"Offer ₹{self.target_price}/kg for {purchase_quantity}kg for processing"
            )
        }

    # ---------------------------------------------
    # Respond to farmer offer
    # ---------------------------------------------

    def respond_to_offer(self, offer, context=None):

        price = offer["price"]
        quantity = offer["quantity"]

        # Processor cannot exceed capacity
        purchase_quantity = min(quantity, self.processing_capacity)

        # Accept if price reasonable
        if price <= self.target_price:

            self.inventory += purchase_quantity

            return {
                "type": "ACCEPT",
                "price": price,
                "quantity": purchase_quantity,
                "message": self.log_action(
                    f"Accepted {purchase_quantity}kg at ₹{price}/kg for processing"
                )
            }

        # Counter if slightly high
        if price <= self.max_price:

            counter_price = (price + self.target_price) / 2
            counter_price = round(counter_price, 2)

            return {
                "type": "COUNTER",
                "price": counter_price,
                "quantity": purchase_quantity,
                "message": self.log_action(
                    f"Counter offer ₹{counter_price}/kg for {purchase_quantity}kg"
                )
            }

        # Reject if too expensive
        return {
            "type": "REJECT",
            "message": self.log_action(
                f"Rejected offer ₹{price}/kg — too expensive for processing"
            )
        }

    # ---------------------------------------------
    # Process stored inventory
    # ---------------------------------------------

    def process_inventory(self, quantity):

        if quantity > self.inventory:

            return {
                "type": "ERROR",
                "message": self.log_action(
                    "Not enough inventory to process"
                )
            }

        self.inventory -= quantity

        processed_output = quantity * 0.9  # assume 10% processing loss

        return {
            "type": "PROCESS_COMPLETE",
            "input_quantity": quantity,
            "output_quantity": processed_output,
            "message": self.log_action(
                f"Processed {quantity}kg into {processed_output}kg product"
            )
        }

    # ---------------------------------------------
    # Processor status
    # ---------------------------------------------

    def get_status(self):

        return {
            "crop_type": self.crop_type,
            "processing_capacity": self.processing_capacity,
            "inventory": self.inventory,
            "target_price": self.target_price
        }