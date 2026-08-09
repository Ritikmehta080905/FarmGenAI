import datetime
from datetime import timezone
from fastapi import APIRouter, HTTPException
from database.db import Database
from nodes.node_hub import hub
from nodes.farmer_node import FarmerNode

router = APIRouter()

@router.post("/node/{node_id}/announce")
async def node_announce(node_id: str, payload: dict):
    if node_id not in hub.nodes:
        hub.register_node(FarmerNode(node_id, payload.get("name", "Local Node")))
    
    node = hub.nodes[node_id]
    msg = await node.announce_supply(
        payload["crop"], payload["quantity"], payload["min_price"]
    )
    await hub.broadcast(node_id, msg)
    return {"status": "broadcast_sent", "message_id": msg.message_id}

@router.get("/node/{node_id}/scenarios")
async def get_node_scenarios(node_id: str, crop: str):
    if node_id not in hub.nodes:
        return {"scenarios": []}
    
    node = hub.nodes[node_id]
    scenarios = node.get_local_scenarios(crop)
    return {"scenarios": scenarios}

@router.post("/node/{node_id}/select")
async def node_select(node_id: str, payload: dict):
    if node_id not in hub.nodes:
         raise HTTPException(status_code=404, detail="Node not found")
    
    node = hub.nodes[node_id]
    crop = payload.get("crop")
    peer_node = payload.get("peer_node")
    
    block = await node.select_scenario(peer_node, crop)
    
    neg_id = block.get("block_id") if isinstance(block, dict) else f"neg_{Database.generate_id('neg')}"
    neg_record = {
        "negotiation_id": neg_id,
        "user_id": node_id,
        "farmer": node.farmer_name,
        "crop": crop,
        "quantity": 1000,
        "status": "NEGOTIATING",
        "peer_node": peer_node,
        "summary": f"Decentralized handshake with {peer_node}",
        "logs": ["Handshake initiated. Consensus reached.", "Verifying node signatures..."],
        "created_at": datetime.datetime.now(timezone.utc).isoformat()
    }
    await Database.update_negotiation_async(neg_id, neg_record)
    await Database.add_history_async(node_id, {"type": "NEGOTIATION_START", **neg_record})
    
    return {"status": "success", "block": block, "negotiation_id": neg_id}
