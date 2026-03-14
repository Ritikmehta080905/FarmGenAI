from agents.base_agent import BaseAgent
from llm.negotiation_reasoning import transport_decision


class TransporterAgent(BaseAgent):

    def __init__(self, min_fee, distance, spoilage_days):
        super().__init__("Transporter")
        self.min_fee = min_fee
        self.distance = distance
        self.spoilage_days = spoilage_days

    def respond(self, client_offer):

        result = transport_decision(
            min_fee=self.min_fee,
            client_offer=client_offer,
            distance=self.distance,
            spoilage_days=self.spoilage_days
        )

        return result
