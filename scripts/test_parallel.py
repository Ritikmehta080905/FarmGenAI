import asyncio
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, "c:/PROJECT/FarmGenAI")

from backend.agents.graph_orchestrator import graph_orchestrator
from database.db import Database, init_db

async def run_test():
    await init_db()
    print("🚀 Starting Parallel Negotiation Test...")
    
    # Simulate a new negotiation job state
    initial_state = {
        "crop": "Tomato",
        "quantity": 500,
        "min_price": 15.0,
        "location": "Nashik",
        "spoilage_days": 4,
        "market_price": 18.0,
        "round": 0,
        "max_rounds": 3,
        "status": "NEGOTIATING",
        "history": [],
        "logs": [],
        "buyers_list": [] # Let the matching engine pick the buyers from DB
    }
    
    print("\n--- Invoking LangGraph AI Workflow ---")
    
    try:
        final_state = await graph_orchestrator.ainvoke(initial_state)
        
        print("\n✅ Negotiation Complete!")
        print(f"Status: {final_state.get('status')}")
        
        print("\n--- Final Deal ---")
        print(json.dumps(final_state.get("deal"), indent=2))
        
        print("\n--- Parallel Market Offers Evaluated ---")
        for offer in final_state.get("market_offers", []):
            print(f"- {offer['buyer_name']}: ₹{offer['price']}/kg ({offer['status']})")
            
        print("\n--- Action Logs ---")
        for log in final_state.get("logs", []):
            if "🎯" in log or "🤝" in log or "🏆" in log or "🚚" in log or "🏢" in log:
                print(log)
                
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
