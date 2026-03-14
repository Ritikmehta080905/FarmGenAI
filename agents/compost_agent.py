from agents.base_agent import BaseAgent


class CompostAgent(BaseAgent):
	def __init__(self, name, base_price=7.5):
		super().__init__(name, "compost")
		self.base_price = base_price

	def make_offer(self, context=None):
		quantity = context.get("quantity", 0) if context else 0
		return {
			"type": "OFFER",
			"price": self.base_price,
			"quantity": quantity,
			"message": self.log_action(
				f"Compost purchase offer at ₹{self.base_price}/kg for {quantity}kg"
			)
		}

	def evaluate_offer(self, offer, context=None):
		return "ACCEPT" if offer.get("price", 0) <= self.base_price else "COUNTER"

	def respond_to_offer(self, offer, context=None):
		offered_price = offer.get("price", 0)
		quantity = offer.get("quantity", 0)

		if offered_price <= self.base_price:
			return {
				"type": "ACCEPT",
				"price": offered_price,
				"quantity": quantity,
				"message": self.log_action(f"Accepted compost purchase at ₹{offered_price}/kg")
			}

		counter_price = round((offered_price + self.base_price) / 2, 2)
		return {
			"type": "COUNTER",
			"price": counter_price,
			"quantity": quantity,
			"message": self.log_action(f"Counter compost price ₹{counter_price}/kg")
		}
