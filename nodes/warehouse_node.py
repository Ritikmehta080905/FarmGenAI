from .base_node import BaseNode
from .p2p_protocol import MessageType, P2PMessage
import logging
import json

class WarehouseNode(BaseNode):
    def __init__(self, node_id: str, location: str, capacity: float):
        super().__init__(node_id, "warehouse")
        self.location = location
        self.capacity = capacity
        self.save_state("storage_info", {"location": location, "available_capacity": capacity})

    async def handle_message(self, msg: P2PMessage) -> list:
        await super().handle_message(msg)
        responses = []
        
        if msg.msg_type == MessageType.SUPPLY_ANNOUNCE:
             # Warehouse listens for high urgency/low quality to offer cold storage
             is_urgent = msg.data.get("urgency") == "High"
             if is_urgent:
                 logging.info(f"Warehouse Node {self.node_id} proposing storage fallback...")
                 
                 storage_data = {
                     "warehouse_name": f"ColdStore-{self.node_id[-4:]}",
                     "cost_per_day": 750,
                     "scenario_type": "storage-fallback",
                     "status": "CAPACITY_AVAILABLE"
                 }
                 responses.append(P2PMessage(self.node_id, msg.from_node, MessageType.MATCH_INTEREST, storage_data))
                 
        elif msg.msg_type == MessageType.FINAL_APPROVAL_REQ:
            # Warehouse signs the storage lease
            sign_resp = P2PMessage(self.node_id, msg.from_node, MessageType.DEAL_SIGNED, {"status": "STORAGE_LEASE_SIGNED"})
            responses.append(sign_resp)
            
        return responses
