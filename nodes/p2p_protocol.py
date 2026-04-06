from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime
import json
from uuid import uuid4

class MessageType(str, Enum):
    # Discovery & Announcement
    SUPPLY_ANNOUNCE = "SUPPLY_ANNOUNCE"
    DEMAND_ANNOUNCE = "DEMAND_ANNOUNCE"
    
    # Negotiation Intent
    MATCH_INTEREST = "MATCH_INTEREST"
    NEGOTIATE_OFFER = "NEGOTIATE_OFFER"
    COUNTER_OFFER = "COUNTER_OFFER"
    
    # Logistics Requests
    LOGISTICS_REQUEST = "LOGISTICS_REQUEST"
    LOGISTICS_QUOTE = "LOGISTICS_QUOTE"
    
    # Agreement Loop
    PROVISIONAL_ACCEPT = "PROVISIONAL_ACCEPT"
    FINAL_APPROVAL_REQ = "FINAL_APPROVAL_REQ"
    DEAL_SIGNED = "DEAL_SIGNED"
    DEAL_FINALIZED = "DEAL_FINALIZED"
    DEAL_CANCELLED = "DEAL_CANCELLED"

class P2PMessage:
    def __init__(self, from_node: str, to_node: str, msg_type: MessageType, data: Dict, signature: Optional[str] = None):
        self.message_id = f"p2p_{uuid4().hex[:12]}"
        self.timestamp = datetime.now().isoformat()
        self.from_node = from_node
        self.to_node = to_node
        self.msg_type = msg_type
        self.data = data
        self.signature = signature or self._generate_sim_signature()

    def _generate_sim_signature(self) -> str:
        # Simulate cryptographic signing for the MVP
        return f"sig_{self.from_node[:6]}_{self.message_id[-6:]}"

    def to_dict(self):
        return {
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "from_node": self.from_node,
            "to_node": self.to_node,
            "msg_type": self.msg_type,
            "data": self.data,
            "signature": self.signature
        }
