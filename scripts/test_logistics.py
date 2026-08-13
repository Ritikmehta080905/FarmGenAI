import asyncio
import sys
import json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, "c:/PROJECT/FarmGenAI")

from backend.agents.graph_orchestrator import dynamic_routing_node, reflection_node

async def run_logistics_test():
    # Simulate a state that reached a DEAL to test dynamic routing (Transport/Warehouse)
    state_deal = {
        "status": "DEAL",
        "crop": "Tomato",
        "quantity": 500,
        "min_price": 15.0,
        "location": "Pune",
        "spoilage_days": 4, # <= 5 triggers warehouse bidding
        "market_price": 18.0,
        "round": 3,
        "history": [],
        "logs": [],
        "deal": {},
        "selected_buyer": {"name": "TestBuyer", "location": "Mumbai"},
        "latest_buyer_offer": 17.5
    }
    
    print("\n--- Testing Parallel Dynamic Routing (Transport & Warehouse) ---")
    routing_res = await dynamic_routing_node(state_deal)
    for log in routing_res.get("logs", []):
        print(log)
        
    print("\nDeal Data Updated:")
    print(json.dumps(routing_res.get("deal"), indent=2))
    
    
    # Simulate a state that REJECTED to test reflection fallback (Processor/Compost)
    state_reject = {
        "status": "REJECT",
        "crop": "Tomato",
        "quantity": 500,
        "min_price": 15.0,
        "location": "Pune",
        "spoilage_days": 10, # > 2 prevents immediate storage
        "market_price": 18.0,
        "round": 3,
        "history": [],
        "logs": [],
        "deal": None,
        "latest_buyer_offer": 14.0
    }
    
    print("\n--- Testing Parallel Reflection Fallback (Processor) ---")
    reflection_res = await reflection_node(state_reject)
    for log in reflection_res.get("logs", []):
        if "⚙️" in log or "♻️" in log or "🏗️" in log:
            print(log)
            
    print("\nFallback Deal Generated:")
    print(json.dumps(reflection_res.get("deal"), indent=2))

if __name__ == "__main__":
    asyncio.run(run_logistics_test())
