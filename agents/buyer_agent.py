# agents/buyer_agent.py
import random
from agents.base_agent import BaseAgent
from intelligence.llm_client import LLMClient

try:
    llm_client = LLMClient()
except Exception:
    llm_client = None

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

        self.budget = budget
        self.max_quantity = max_quantity
        self.target_price = target_price
        self.inventory = 0
        self.location = location

    def evaluate_offer(self, offer, context=None):
        # Even if it's below target, we try to counter once to see 
        # if the farmer is desperate/flexible.
        if offer["price"] <= self.target_price * 0.95:
            return "ACCEPT"
        return "COUNTER"

    def make_offer(self, context=None):
        # Opening bid is low (approx 25% below target)
        offer_price = round(max(1.0, self.target_price * 0.75 + random.uniform(-0.5, 0.5)), 2)
        quantity = min(self.max_quantity, random.randint(100, 500))
        message = self.log_action(f"I initial bid ₹{offer_price}/kg for {quantity}kg")
        return {
            "price": offer_price,
            "quantity": quantity,
            "message": message
        }

    # ---------------------------------------------
    # Respond to farmer offer using LLM
    # ---------------------------------------------
    def respond_to_offer(self, offer, context=None):

        market_price = context.get("market_price", self.target_price) if context else self.target_price

        llm_decision = None
        if llm_client:
            llm_decision = llm_client.negotiation_reasoning(
                role="Buyer",
                offered_price=offer["price"],
                target_price=self.target_price,
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
        counter_price = llm_decision.get("counter_price", self.target_price)
        reason = llm_decision.get("reason", "")

        if decision == "ACCEPT":
            purchasable_qty = min(offer["quantity"], self.max_quantity, self.budget // offer["price"])
            self.inventory += purchasable_qty
            self.budget -= purchasable_qty * offer["price"]
            return {
                "type": "ACCEPT",
                "price": offer["price"],
                "quantity": purchasable_qty,
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
            self.target_price = counter_price
            return {
                "type": "COUNTER",
                "price": counter_price,
                "quantity": offer["quantity"],
                "message": self.log_action(f"COUNTER ₹{counter_price}/kg: {reason}")
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
        quantity = offer["quantity"]

        # Accept if it's very close to our target (within 3%)
        if price <= self.target_price * 1.03:
            return {
                "decision": "ACCEPT",
                "counter_price": None,
                "reason": "This price is within my procurement margin boundaries."
            }

        # REJECT if it's vastly over current market price
        if price > max(self.target_price, market_price) * 1.4:
            return {
                "decision": "REJECT",
                "counter_price": None,
                "reason": "This price is far above local market averages."
            }

        # Slow incremental counter to show a real negotiation 'dance'
        # Only move 20% toward their offer per round
        gap = price - self.target_price
        adjusted_price = round(self.target_price + (gap * 0.2) + random.uniform(0.1, 0.4), 2)
        adjusted_price = min(price, adjusted_price)

        return {
            "decision": "COUNTER",
            "counter_price": adjusted_price,
            "reason": "I'm offering a slight increase to reach a compromise."
        }