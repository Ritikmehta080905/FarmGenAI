from agents.buyer_agent import BuyerAgent
from agents.farmer_agent import FarmerAgent
from agents.processor_agent import ProcessorAgent
from agents.warehouse_agent import WarehouseAgent
from agents.transporter_agent import TransporterAgent


class AgentRegistry:
    def __init__(self):
        self.agents = {}

    def register_agent(self, agent_type, agent_instance):
        self.agents[agent_type] = agent_instance

    def get_agent(self, agent_type):
        return self.agents.get(agent_type)

    def create_agents(self):
        # Example initialization
        self.register_agent("buyer", BuyerAgent(budget=25))
        self.register_agent("farmer", FarmerAgent(min_price=18, spoilage_days=3))
        self.register_agent("processor", ProcessorAgent(demand_price=20))
        self.register_agent("warehouse", WarehouseAgent(storage_cost=2))
        self.register_agent("transporter", TransporterAgent(min_fee=5, distance=100, spoilage_days=3))
