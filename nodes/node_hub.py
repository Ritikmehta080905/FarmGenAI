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
        logging.info(f"Node Registered: {node.node_id} ({node.role})")

    async def broadcast(self, sender_id: str, message: P2PMessage):
        """Discovery Relay: Distribute protocol events and push to frontend sockets."""
        logging.info(f"P2P BROADCAST: {message.msg_type} from {sender_id}")
        
        # Link to Frontend via WebSocket for real-time monitoring
        from backend.websocket.agent_updates import agent_update_hub
        asyncio.create_task(agent_update_hub.broadcast({
            "event": "NEGOTIATION_LOG",
            "message": f"🌐 Network Broadcast: {message.msg_type} from Node {sender_id[:6]}",
            "agent_type": "system",
            "type": "p2p_network"
        }))

        deliveries = []
        for nid, node in self.nodes.items():
            if nid != sender_id:
                deliveries.append(node.handle_message(message))
        
        peer_replies = await asyncio.gather(*deliveries)
        
        for reply_list in peer_replies:
            if reply_list:
                for r in reply_list:
                    if r and r.to_node in self.nodes:
                        await self.nodes[r.to_node].handle_message(r)
                        # Log Peer direct response
                        asyncio.create_task(agent_update_hub.broadcast({
                            "event": "NEGOTIATION_LOG",
                            "message": f"📩 P2P Direct: {r.msg_type} from {r.from_node[:6]} to {r.to_node[:6]}",
                            "agent_type": "system",
                            "type": "p2p_direct"
                        }))

    async def direct_send(self, from_node: str, to_node: str, message: P2PMessage):
        """Targeted P2P: Direct communication between nodes."""
        if to_node in self.nodes:
            logging.info(f"P2P DIRECT: {message.msg_type} to {to_node}")
            return await self.nodes[to_node].handle_message(message)
        return None

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

# Initial Peer Network Discovery (Full Supply Chain)
async def bootstrap_peer_network():
    # Instantiate nodes with isolated states
    hub.register_node(FarmerNode("node_f_ramesh", "Ramesh Farmer"))
    hub.register_node(BuyerNode("node_b_bigstore", "MegaMart Buyer", ["Tomato", "Onion"]))
    hub.register_node(BuyerNode("node_b_localseller", "Local Haat", ["Potato", "Cabbage"]))
    
    # Advanced Stakeholders
    hub.register_node(TransporterNode("node_l_fastrack", "Fastrack Logistics", 1500))
    hub.register_node(TransporterNode("node_l_eco", "EcoFreight", 1200))
    hub.register_node(WarehouseNode("node_w_coldstore", "Nashik North", 5000))
    hub.register_node(FactoryNode("node_f_ketchup", "Heinz Processing", 200))
