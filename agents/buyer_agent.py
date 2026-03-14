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
        if offer["price"] <= self.target_price:
            return "ACCEPT"
        return "COUNTER"

    # ---------------------------------------------
    # Initial offer
    # ---------------------------------------------
    def make_offer(self, context=None):
        offer_price = max(1, self.target_price - random.randint(1, 3))
        quantity = min(self.max_quantity, random.randint(100, 500))
        message = self.log_action(f"I offer ₹{offer_price}/kg for {quantity}kg")
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

        if price <= self.target_price:
            return {
                "decision": "ACCEPT",
                "counter_price": None,
                "reason": "price is within target"
            }

        if price > max(self.target_price, market_price) * 1.25:
            return {
                "decision": "REJECT",
                "counter_price": None,
                "reason": "offer is significantly above market"
            }

        max_affordable_qty = max(1, int(self.budget // max(price, 1)))
        if quantity > max_affordable_qty:
            adjusted_price = round(min(self.target_price, market_price), 2)
        else:
            adjusted_price = round((self.target_price + market_price) / 2, 2)

        return {
            "decision": "COUNTER",
            "counter_price": adjusted_price,
            "reason": "countering to fit budget and target margin"
        }