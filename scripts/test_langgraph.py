import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.graph_orchestrator import workflow

async def run_test():
    app = workflow.compile()
    
    initial_state = {
        "crop": "Soybean",
        "quantity": 500,
        "min_price": 45,
        "location": "Pune",
        "spoilage_days": 180,
        "market_price": 53.28,
        "round": 0,
        "max_rounds": 3,
        "history": [],
        "logs": [],
        "buyers_list": [
            {
                "id": "buyer_123",
                "name": "SuperFresh Retail",
                "target_price": 22,
                "budget": 15000,
                "max_quantity": 500,
                "location": "Nashik",
                "strategy": "Premium Quality"
            }
        ]
    }
    
    print("Starting Conversational Negotiation Flow...")
    final_state = await app.ainvoke(initial_state)
    
    print("\n\n====== NEGOTIATION LOGS ======\n")
    for log in final_state.get("logs", []):
        print(log)

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(run_test())
