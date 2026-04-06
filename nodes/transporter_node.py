from .base_node import BaseNode
from .p2p_protocol import MessageType, P2PMessage
import logging
import json

class TransporterNode(BaseNode):
    def __init__(self, node_id: str, company_name: str, base_fee: float):
        super().__init__(node_id, "transporter")
        self.company_name = company_name
        self.base_fee = base_fee
        self.save_state("company_info", {"name": company_name, "base_fee": base_fee})

    async def handle_message(self, msg: P2PMessage) -> list:
        await super().handle_message(msg)
        
        responses = []
        if msg.msg_type == MessageType.SUPPLY_ANNOUNCE:
            # Automatic Quote generation for logistics
            logging.info(f"Logistics Node {self.node_id} generating auto-quote for {msg.from_node}...")
            
            # Simple AI/Rule logic for quoting
            dist_km = 45 # Simulated
            quote_price = self.base_fee + (dist_km * 12.5)
            
            quote_data = {
                "transporter_name": self.company_name,
                "quote_price": round(quote_price, 2),
                "capacity": 2000,
                "scenario_type": "logistics-active"
            }
            
            # Send LOGISTICS_QUOTE back to the initiating farmer
            reply = P2PMessage(self.node_id, msg.from_node, MessageType.LOGISTICS_QUOTE, quote_data)
            responses.append(reply)
            
        elif msg.msg_type == MessageType.FINAL_APPROVAL_REQ:
            # Transporter signs the deal to confirm availability
            logging.info(f"Logistics Node {self.node_id} signing final transport contract...")
            sign_resp = P2PMessage(self.node_id, msg.from_node, MessageType.DEAL_SIGNED, {"status": "TRANSPORT_CONFIRMED"})
            responses.append(sign_resp)
            
        return responses
