# agents/farmer_agent.py
import random
from agents.base_agent import BaseAgent
from intelligence.llm_client import LLMClient

try:
    llm_client = LLMClient()
except Exception:
    llm_client = None

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

        self.crop = crop
        self.quantity = quantity
        self.location = location

        self.min_price = min_price
        # Start at a more ambitious price (market-aligned + buffer) to allow room to haggle
        self.current_price = min_price + random.randint(8, 12)

        self.shelf_life = shelf_life
        self.min_sale_quantity = min_sale_quantity

        # fallback options
        self.has_storage_option = True
        self.has_processor_option = True

    def evaluate_offer(self, offer, context=None):
        # Hybrid Reasoning: If it meets my high current target (or is VERY close), ACCEPT.
        # Otherwise COUNTER even if it's over min, to see if they can pay more.
        if offer["price"] >= self.current_price * 0.98:
            return "ACCEPT"
        return "COUNTER"

    # ---------------------------------------------
    # Farmer initial offer
    # ---------------------------------------------
    def make_offer(self, context=None):
        message = self.log_action(
            f"Selling {self.quantity}kg {self.crop} at ₹{self.current_price}/kg"
        )
        return {
            "price": self.current_price,
            "quantity": self.quantity,
            "message": message
        }

    # ---------------------------------------------
    # Respond to buyer offer using LLM
    # ---------------------------------------------
    def respond_to_offer(self, offer, context=None):

        market_price = context.get("market_price", self.current_price) if context else self.current_price

        llm_decision = None
        if llm_client:
            llm_decision = llm_client.negotiation_reasoning(
                role="Farmer",
                offered_price=offer["price"],
                target_price=self.current_price,
                market_price=market_price,
                quantity=offer["quantity"]
            )

        if not llm_decision:
            fallback = self._fallback_decision(offer, market_price)
            llm_decision = {
                "decision": fallback["decision"],
                "counter_price": fallback["counter_price"],
                "reason": fallback["reason"]
            }

        decision = llm_decision.get("decision", "COUNTER")
        counter_price = llm_decision.get("counter_price", self.current_price)
        reason = llm_decision.get("reason", "")

        if decision == "ACCEPT":
            accepted_qty = min(offer["quantity"], self.quantity)
            self.quantity -= accepted_qty
            return {
                "type": "ACCEPT",
                "price": offer["price"],
                "quantity": accepted_qty,
                "message": self.log_action(f"ACCEPTED ₹{offer['price']}/kg: {reason}")
            }

        elif decision == "REJECT":
            return {
                "type": "REJECT",
                "price": offer["price"],
                "quantity": offer["quantity"],
                "message": self.log_action(f"REJECTED offer ₹{offer['price']}/kg: {reason}")
            }

        elif decision == "COUNTER":
            # Update internal price to LLM-suggested counter
            self.current_price = max(counter_price, self.min_price)
            return {
                "type": "COUNTER",
                "price": self.current_price,
                "quantity": offer["quantity"],
                "message": self.log_action(f"COUNTER ₹{self.current_price}/kg: {reason}")
            }

        fallback = self._fallback_decision(offer, market_price)
        return {
            "type": fallback["decision"],
            "price": fallback["counter_price"] if fallback["decision"] == "COUNTER" else offer["price"],
            "quantity": offer["quantity"],
            "message": self.log_action(f"{fallback['decision']} at ₹{offer['price']}/kg: {fallback['reason']}")
        }

    def _fallback_decision(self, offer, market_price):
        price = offer["price"]
        # Accept if it's very close to our ambitious target (within 2%)
        if price >= self.current_price * 0.98:
            return {
                "decision": "ACCEPT",
                "counter_price": None,
                "reason": "Price meets our target expectation."
            }

        if price < self.min_price * 0.9:
            return {
                "decision": "REJECT",
                "counter_price": None,
                "reason": "Offer is far below sustainabily levels."
            }

        # Hybrid Step: Move only 20% of the gap per round to simulate 'haggling'
        gap = self.current_price - price
        counter_price = round(price + (gap * 0.2) + random.uniform(0.1, 0.4), 2)
        counter_price = max(self.min_price, counter_price)
        
        return {
            "decision": "COUNTER",
            "counter_price": counter_price,
            "reason": "I am looking for a price closer to my target, though I am willing to meet part-way."
        }