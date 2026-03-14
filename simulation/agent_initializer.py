from agents.buyer_agent import BuyerAgent
from agents.compost_agent import CompostAgent
from agents.farmer_agent import FarmerAgent
from agents.processor_agent import ProcessorAgent
from agents.transporter_agent import TransporterAgent
from agents.warehouse_agent import WarehouseAgent


def initialize_agents(config: dict):
	farmer = FarmerAgent(
		name=config.get("farmer_name", "FarmerAgent"),
		crop=config["crop"],
		quantity=config["quantity"],
		min_price=config["min_price"],
		shelf_life=config.get("shelf_life", 3),
		location=config.get("location", "Unknown")
	)
	buyer = BuyerAgent(
		name=config.get("buyer_name", "BuyerAgent"),
		budget=config.get("buyer_budget", config["quantity"] * config["min_price"] * 1.2),
		max_quantity=config.get("buyer_max_quantity", config["quantity"]),
		target_price=config.get("buyer_target_price", config["min_price"] + 1)
	)
	warehouse = WarehouseAgent(
		name="WarehouseAgent",
		capacity=config.get("warehouse_capacity", 4000),
		storage_cost_per_kg=config.get("storage_cost_per_kg", 1.8),
		location=config.get("location", "Unknown")
	)
	processor = ProcessorAgent(
		name="ProcessorAgent",
		crop_type=config["crop"],
		processing_capacity=config.get("processor_capacity", config["quantity"]),
		processing_cost_per_kg=config.get("processing_cost_per_kg", 2.0),
		target_price=config.get("processor_target_price", config["min_price"] - 1),
		max_price=config.get("processor_max_price", config["min_price"] + 2)
	)
	transporter = TransporterAgent(
		name="TransporterAgent",
		vehicle_capacity=config.get("transporter_capacity", 2000),
		cost_per_km_per_kg=config.get("cost_per_km_per_kg", 0.03),
		base_fee=config.get("base_fee", 450)
	)
	compost = CompostAgent(name="CompostAgent", base_price=config.get("compost_price", 8))

	return {
		"farmer": farmer,
		"buyer": buyer,
		"warehouse": warehouse,
		"processor": processor,
		"transporter": transporter,
		"compost": compost,
	}
