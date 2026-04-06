from .base_node import BaseNode
from .p2p_protocol import MessageType, P2PMessage
import logging
import json

class FactoryNode(BaseNode):
    def __init__(self, node_id: str, factory_name: str, min_qty: float):
        super().__init__(node_id, "factory")
        self.factory_name = factory_name
        self.min_qty = min_qty
        self.save_state("factory_info", {"name": factory_name, "processing_capacity": 5000})

    async def handle_message(self, msg: P2PMessage) -> list:
        await super().handle_message(msg)
        responses = []
        
        if msg.msg_type == MessageType.SUPPLY_ANNOUNCE:
             # Factory acts as fallback or secondary demand
             quantity = msg.data.get("quantity", 0)
             if quantity >= self.min_qty:
                 logging.info(f"Factory Node {self.node_id} interested in surplus {msg.data.get('crop')}...")
                 
                 # Price is typically lower for industrial processing
                 factory_price = msg.data.get("min_price", 0) * 0.85
                 
                 factory_data = {
                     "factory_name": self.factory_name,
                     "price": round(factory_price, 2),
                     "scenario_type": "industrial-fallback",
                     "status": "PROCESSING_DEMAND"
                 }
                 responses.append(P2PMessage(self.node_id, msg.from_node, MessageType.MATCH_INTEREST, factory_data))
                 
        elif msg.msg_type == MessageType.FINAL_APPROVAL_REQ:
            # Factory signs to finalize fallback deal
            sign_resp = P2PMessage(self.node_id, msg.from_node, MessageType.DEAL_SIGNED, {"status": "FACTORY_CONFIRMED"})
            responses.append(sign_resp)
            
        return responses
