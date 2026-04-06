import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.farmer_agent import FarmerAgent
from agents.buyer_agent import BuyerAgent
from agents.warehouse_agent import WarehouseAgent
from agents.processor_agent import ProcessorAgent
from agents.compost_agent import CompostAgent
from negotiation_engine.negotiation_manager import NegotiationManager

def run_test():
    print("🚀 Running Multi-Agent Supply Chain Negotiation Test...")

    farmer = FarmerAgent(name="FarmerAgent", crop="Tomato", quantity=1000, min_price=35, shelf_life=4) # high min_price to trigger escalation
    
    # Discovery of multiple buyers
    buyers = [
        BuyerAgent(name="Market Retailer", budget=20000, max_quantity=600, target_price=18),
        BuyerAgent(name="Export Link", budget=50000, max_quantity=1000, target_price=22)
    ]
    
    # Fallback agents
    warehouse = WarehouseAgent(name="ColdStore", capacity=5000, storage_cost_per_kg=1.5, location="Nashik")
    processor = ProcessorAgent(name="Ketchup Factory", crop_type="Tomato", processing_capacity=2000, processing_cost_per_kg=2.0, target_price=15, max_price=20)
    compost = CompostAgent(name="EcoFarm", base_price=8)

    manager = NegotiationManager(
        farmer=farmer,
        buyers=buyers,
        warehouse=warehouse,
        processor=processor,
        compost=compost
    )

    print("\n--- Negotiation Thread Start ---\n")
    result = manager.start_negotiation(market_price=20, quantity=1000)

    for entry in manager.log:
        print(f" > {entry}")

    print("\n" + "="*50)
    print(f"🏁 Final Result: {result['state']}")
    print(f"📌 Summary: {result['summary']}")
    print("="*50)

if __name__ == "__main__":
    run_test()