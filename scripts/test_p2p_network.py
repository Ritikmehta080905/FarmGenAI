import sys
import os
import asyncio
import logging

# Set up path and logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
logging.basicConfig(level=logging.INFO)

from nodes.node_hub import hub, bootstrap_peer_network
from nodes.p2p_protocol import MessageType

async def run_p2p_test():
    print("\n--- 🌐 DISCOVERING P2P PEERS ---")
    await bootstrap_peer_network()
    print(f"Nodes Active: {list(hub.nodes.keys())}")

    print("\n--- 📢 FARMER ANNOUNCING SUPPLY ---")
    farmer = hub.nodes["node_f_ramesh"]
    # 1. Announce supply
    msg = await farmer.announce_supply(crop="Tomato", quantity=500, min_price=18)
    
    # 2. Broadcast to network (this will trigger autonomous Buyer responses)
    await hub.broadcast(farmer.node_id, msg)
    
    # Give some time for async processing if needed (though hub is sequential in my edit)
    await asyncio.sleep(1)

    print("\n--- 🧠 FARMER ANALYZING SCENARIOS ---")
    scenarios = farmer.get_local_scenarios(crop="Tomato")
    if not scenarios:
        print("❌ No scenarios found. P2P interest matching failed.")
        return

    for i, s in enumerate(scenarios):
        print(f"Scenario {i+1}: {s['type']} with {s['peer_node']} (Score: {s['score']})")

    # 3. Select top scenario (multi-party consensus handshake)
    best = scenarios[0]
    print(f"\n--- ✍️ SIGNING DEAL WITH {best['peer_node']} ---")
    result = await farmer.select_scenario(best['peer_node'], "Tomato")
    
    if result and result.get("status") == "FINALIZED":
        print(f"✅ SUCCESS: Deal finalized at Block {result['block_id']}")
        print(f"Hash: {result['hash']}")
    else:
        print(f"❌ FAILED: Deal did not reach consensus. {result.get('reason', 'Unknown error')}")

    print("\n--- 📜 SHARED AUDIT LEDGER ---")
    for block in hub.audit_ledger:
        print(f"[{block['block_id']}] {block['data']['farmer']} <-> {block['data']['partner']} | Hash: {block['hash']}")

if __name__ == "__main__":
    asyncio.run(run_p2p_test())
