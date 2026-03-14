from agents.base_agent import BaseAgent
from llm.negotiation_reasoning import farmer_decision


class FarmerAgent(BaseAgent):

    def __init__(self, min_price, spoilage_days):
        super().__init__("Farmer")
        self.min_price = min_price
        self.spoilage_days = spoilage_days

    def respond(self, buyer_offer):

        result = farmer_decision(
            min_price=self.min_price,
            buyer_offer=buyer_offer,
            spoilage_days=self.spoilage_days
        )

        return result