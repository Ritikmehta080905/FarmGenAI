from agents.base_agent import BaseAgent
from llm.negotiation_reasoning import warehouse_decision


class WarehouseAgent(BaseAgent):

    def __init__(self, storage_cost, spoilage_days, market_price):
        super().__init__("Warehouse")
        self.storage_cost = storage_cost
        self.spoilage_days = spoilage_days
        self.market_price = market_price

    def evaluate_storage(self):

        result = warehouse_decision(
            storage_cost=self.storage_cost,
            spoilage_days=self.spoilage_days,
            market_price=self.market_price
        )

        return result