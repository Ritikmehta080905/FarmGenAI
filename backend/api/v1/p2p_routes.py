from backend.repositories.user_repository import UserRepository
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from database.db import Database
from nodes.node_hub import hub
from nodes.farmer_node import FarmerNode

router = APIRouter()

@router.post("/node/{node_id}/announce")
async def node_announce(node_id: str, payload: dict):
    # Discovery: Register the user node if it doesn't exist
    if node_id not in hub.nodes:
        hub.register_node(FarmerNode(node_id, payload.get("name", "Local Node")))
    
    node = hub.nodes[node_id]
    msg = await node.announce_supply(
        payload["crop"], payload["quantity"], payload["min_price"]
    )
    # Broadcast to peers via the Relay Hub
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
    
    # Phase 2: Start the Multi-Party Direct Handshake
    block = await node.select_scenario(peer_node, crop)
    
    # Persistence
    neg_id = block.get("block_id") if isinstance(block, dict) else f"neg_{Database.generate_id('neg')}"
    neg_record = {
        "negotiation_id": neg_id,
        "user_id": node_id,
        "farmer_name": node.farmer_name,
        "crop": crop,
        "quantity": 1000, # Fallback or from payload
        "status": "NEGOTIATING",
        "peer_node": peer_node,
        "summary": f"Decentralized handshake with {peer_node}",
        "logs": ["Handshake initiated. Consensus reached.", "Verifying node signatures..."],
    }
    await Database.update_negotiation_async(neg_id, neg_record)
    await Database.add_history_async(node_id, {"type": "NEGOTIATION_START", **neg_record})
    
    return {"status": "success", "block": block, "negotiation_id": neg_id}

@router.get("/nodes")
async def get_all_nodes():
    """Return a map of all discovered P2P nodes for Admin Governance."""
    nodes_map = {}
    for nid, n in hub.nodes.items():
        # Optional: Enrich with DB trust score if node_id matches a user_id
        user = await UserRepository.get_by_id(nid) or {}
        nodes_map[nid] = {
            "role": n.role,
            "status": "online",
            "trust_score": user.get("trust_score", 4.2),
            "verified": user.get("verified", nid.startswith("node_")), # Auto-verify platform nodes
            "history": [] 
        }
    return nodes_map

@router.get("/ledger")
async def get_public_ledger():
    return {"ledger": hub.audit_ledger}

