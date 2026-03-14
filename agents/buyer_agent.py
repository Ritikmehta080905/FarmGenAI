from agents.base_agent import BaseAgent
from llm.negotiation_reasoning import buyer_decision


class BuyerAgent(BaseAgent):

    def __init__(self, max_price, spoilage_days):
        super().__init__("Buyer")
        self.max_price = max_price
        self.spoilage_days = spoilage_days

    def respond(self, farmer_ask):

        result = buyer_decision(
            max_price=self.max_price,
            farmer_ask=farmer_ask,
            spoilage_days=self.spoilage_days
        )

        return result