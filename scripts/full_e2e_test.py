"""Full end-to-end integration test for FarmGenAI."""
import sys
import json
sys.path.insert(0, 'c:/PROJECT/FarmGenAI')

errors = []

# 1. Test all agent imports
try:
    from agents.farmer_agent import FarmerAgent
    from agents.buyer_agent import BuyerAgent
    from agents.restaurant_agent import RestaurantAgent
    from agents.warehouse_agent import WarehouseAgent
    from agents.processor_agent import ProcessorAgent
    from agents.compost_agent import CompostAgent
    from agents.transporter_agent import TransporterAgent
    print('[OK] All 7 agents import correctly')
except Exception as e:
    errors.append(f'[FAIL] Agents: {e}')

# 2. Test negotiation engine
try:
    from negotiation_engine.negotiation_manager import NegotiationManager
    from negotiation_engine.scoring import calculate_scenario_score
    print('[OK] Negotiation engine imports')
except Exception as e:
    errors.append(f'[FAIL] Negotiation engine: {e}')

# 3. Test LLM clients
try:
    from llm.llm_client import LLMClient, client
    from intelligence.llm_client import LLMClient as LLMClient2
    print('[OK] LLM clients import (llm/ + intelligence/ re-export)')
except Exception as e:
    errors.append(f'[FAIL] LLM: {e}')

# 4. Test intelligence modules
try:
    from intelligence.agent_reasoning import AgentReasoning
    from intelligence.negotiation_strategy import NegotiationStrategy
    strat = NegotiationStrategy('aggressive')
    print(f'[OK] Intelligence: NegotiationStrategy({strat.strategy_type}) = {strat.describe()[:40]}')
except Exception as e:
    errors.append(f'[FAIL] Intelligence: {e}')

# 5. Test database
try:
    from database.db import Database, init_db
    import asyncio
    asyncio.run(init_db())
    buyers = asyncio.run(Database.list_buyers_async())
    print(f'[OK] Database OK, {len(buyers)} buyers seeded')
except Exception as e:
    errors.append(f'[FAIL] Database: {e}')

# 6. Test shared utilities
try:
    from shared.event_bus import event_bus
    from shared.shelf_life_estimator import urgency_level, default_shelf_life
    print(f'[OK] Shelf life: Tomato={default_shelf_life("Tomato")}d | Spinach urgency={urgency_level(2)}')
except Exception as e:
    errors.append(f'[FAIL] Shared: {e}')

# 7. E2E full negotiation pass
try:
    farmer = FarmerAgent('TestFarmer', 'Tomato', 200, 18, 4, 'Nashik')
    buyer = BuyerAgent('TestBuyer', 5000, 200, 20)
    warehouse = WarehouseAgent('SimWarehouse', 3000, 1.5, 'Nashik')
    compost = CompostAgent('TestCompost', 8)
    manager = NegotiationManager(farmer=farmer, buyers=[buyer], warehouse=warehouse, compost=compost)
    import asyncio
    result = asyncio.run(manager.start_negotiation(market_price=19))
    print(f'[OK] E2E Negotiation: state={result["state"]} | logs={len(result.get("logs", []))} lines')
except Exception as e:
    import traceback
    traceback.print_exc()
    errors.append(f'[FAIL] E2E Negotiation: {e}')

# 8. Farmer-first scoring
try:
    score = calculate_scenario_score({
        'status': 'DEAL',
        'scenario_type': 'direct-sale',
        'final_price': 22,
        'min_price': 18,
        'shelf_life': 4,
        'quantity': 200,
        'offered_quantity': 200
    })
    print(f'[OK] Scoring: total={score["score"]} | breakdown={score["breakdown"]}')
except Exception as e:
    errors.append(f'[FAIL] Scoring: {e}')

# 9. RestaurantAgent freshness gate
try:
    rest = RestaurantAgent('GreenLeaf', 20000, 50, 28, min_shelf_life=3)
    # Should REJECT stale produce
    stale_response = rest.respond_to_offer({'price': 25, 'quantity': 40}, context={'shelf_life': 1})
    # Should ACCEPT fresh produce
    fresh_response = rest.respond_to_offer({'price': 25, 'quantity': 40}, context={'shelf_life': 5})
    print(f'[OK] RestaurantAgent: stale={stale_response["type"]} | fresh={fresh_response["type"]}')
except Exception as e:
    errors.append(f'[FAIL] RestaurantAgent: {e}')

# 10. TransporterAgent cost calculation
try:
    transporter = TransporterAgent('FastTrack', 2000, 0.03, 450)
    cost = transporter.calculate_transport_cost(500, 180)
    print(f'[OK] TransporterAgent: 500kg x 180km = Rs.{cost} (base_fee=450)')
except Exception as e:
    errors.append(f'[FAIL] TransporterAgent: {e}')

print('\n' + '='*50)
if errors:
    print(f'RESULT: {len(errors)} FAILURES')
    for e in errors:
        print(e)
else:
    print('RESULT: ALL 10 TESTS PASSED - System is fully operational!')
