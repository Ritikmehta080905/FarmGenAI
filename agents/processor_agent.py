from agents.base_agent import BaseAgent
from llm.negotiation_reasoning import processor_decision


class ProcessorAgent(BaseAgent):

    def __init__(self, demand_price, quantity, spoilage_days):
        super().__init__("Processor")
        self.demand_price = demand_price
        self.quantity = quantity
        self.spoilage_days = spoilage_days

    def check_purchase(self, offered_price):

        result = processor_decision(
            demand_price=self.demand_price,
            offered_price=offered_price,
            quantity=self.quantity,
            spoilage_days=self.spoilage_days
        )

        return result