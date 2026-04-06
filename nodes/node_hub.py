import asyncio
import logging
from uuid import uuid4
from typing import Dict, List, Any
from .p2p_protocol import MessageType, P2PMessage
from .farmer_node import FarmerNode
from .buyer_node import BuyerNode
from .transporter_node import TransporterNode
from .factory_node import FactoryNode
from .warehouse_node import WarehouseNode

# Shared Hub for discovery and protocol relay
class NodeHub:
    def __init__(self):
        self.nodes = {} # node_id -> node instance
        self.audit_ledger = [] # Public signed deal records (simulated blockchain)

    def register_node(self, node):
        self.nodes[node.node_id] = node
        print(f"DEBUG: Hub registering {node.node_id}. Total: {len(self.nodes)}")
        logging.info(f"Node Registered: {node.node_id} ({node.role})")

    async def broadcast(self, sender_id: str, message: P2PMessage):
        """Discovery Relay: Distribute protocol events and push to frontend sockets."""
        logging.info(f"P2P BROADCAST: {message.msg_type} from {sender_id}")
        
        # Link to Frontend via WebSocket for real-time monitoring
        from backend.websocket.agent_updates import agent_update_hub
        agent_update_hub.broadcast_threadsafe({
            "event": "NEGOTIATION_LOG",
            "message": f"🌐 Network Broadcast: {message.msg_type} from Node {sender_id[:6]}",
            "agent_type": "system",
            "type": "p2p_network"
        })

        # Collect all peer nodes except sender
        peers = [nid for nid in self.nodes if nid != sender_id]
        
        # Process in parallel
        tasks = [self.direct_send(sender_id, pid, message) for pid in peers]
        await asyncio.gather(*tasks)

    async def direct_send(self, from_node: str, to_node: str, message: P2PMessage):
        """Targeted P2P: Direct communication between nodes. Handles recursive replies."""
        if to_node not in self.nodes:
            return None

        # Deliver message
        node = self.nodes[to_node]
        replies = await node.handle_message(message)
        
        # Log to UI
        from backend.websocket.agent_updates import agent_update_hub
        agent_update_hub.broadcast_threadsafe({
            "event": "NEGOTIATION_LOG",
            "message": f"📩 P2P Direct: {message.msg_type} from {from_node[:6]} to {to_node[:6]}",
            "agent_type": "system",
            "type": "p2p_direct"
        })

        # Process any automated responses from the receiving node's agent
        if replies:
            if isinstance(replies, P2PMessage):
                replies = [replies]
            
            for r in replies:
                # Recursive call to handle response chain (e.g. OFFER -> COUNTER_OFFER)
                await self.direct_send(r.from_node, r.to_node, r)
        
        return replies

    def record_signed_deal(self, deal_data: Dict):
        """Final Agreement: Append a signed contract to the immutable audit log."""
        self.audit_ledger.append({
            "block_id": f"blk_{len(self.audit_ledger) + 1}",
            "data": deal_data,
            "hash": f"h_{uuid4().hex[:12]}",
            "status": "FINALIZED"
        })
        return self.audit_ledger[-1]

# Global hub instance for the MVP runtime
hub = NodeHub()
print(f"DEBUG: Hub Global Instance Created: {id(hub)}")

# Initial Peer Network Discovery (Full Supply Chain)
async def bootstrap_peer_network():
    logging.info("🚀 P2P PEER DISCOVERY: Bootstrapping supply chain nodes...")
    # Instantiate nodes with isolated states
    hub.register_node(FarmerNode("node_f_ramesh", "Ramesh Farmer"))
    hub.register_node(BuyerNode("node_b_bigstore", "MegaMart Buyer", ["Tomato", "Onion"]))
    hub.register_node(BuyerNode("node_b_localseller", "Local Haat", ["Potato", "Cabbage"]))
    
    # Advanced Stakeholders
    hub.register_node(TransporterNode("node_l_fastrack", "Fastrack Logistics", 1500))
    hub.register_node(TransporterNode("node_l_eco", "EcoFreight", 1200))
    hub.register_node(WarehouseNode("node_w_coldstore", "Nashik North", 5000))
    hub.register_node(FactoryNode("node_f_ketchup", "Heinz Processing", 200))
    logging.info(f"✅ Bootstrapping complete. {len(hub.nodes)} nodes online.")
