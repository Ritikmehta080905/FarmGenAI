from .base_node import BaseNode
from .p2p_protocol import MessageType, P2PMessage
import json
import logging

class FarmerNode(BaseNode):
    def __init__(self, node_id: str, farmer_name: str):
        super().__init__(node_id, "farmer")
        self.farmer_name = farmer_name
        self.active_broadcasts = {} # crop -> msg_id
        
    async def announce_supply(self, crop: str, quantity: float, min_price: float, logistics: bool = True):
        """Broadcast Supply to all discovered nodes."""
        data = {
            "farmer_name": self.farmer_name,
            "crop": crop,
            "quantity": quantity,
            "min_price": min_price,
            "location": self.get_state("location") or "Nashik",
            "quality": "A"
        }
        msg = P2PMessage(self.node_id, "BROADCAST", MessageType.SUPPLY_ANNOUNCE, data)
        self.active_broadcasts[crop] = msg.message_id
        self.record_p2p_event(msg)
        return msg

    async def handle_message(self, msg: P2PMessage):
        await super().handle_message(msg)
        
        if msg.msg_type == MessageType.MATCH_INTEREST:
            logging.info(f"Node {self.node_id} received INTEREST from {msg.from_node}")
            # Local logic: Store peer interest to build scenarios
            interests = self.get_state(f"interests_{msg.data.get('crop')}") or []
            interests.append(msg.to_dict())
            self.save_state(f"interests_{msg.data.get('crop')}", interests)
            
        elif msg.msg_type == MessageType.NEGOTIATE_OFFER:
            # Handle direct negotiation with a specific buyer
            pass
            
    async def select_scenario(self, peer_node_id: str, crop: str):
        """Phase 2: Farmer selects a peer scenario. Initiates multi-party handshake."""
        logging.info(f"Node {self.node_id} initiating FINAL APPROVAL with {peer_node_id}")
        
        # 1. Send provisional acceptance to the selected peer
        data = {"crop": crop, "status": "PROVISIONAL_ACCEPT"}
        msg = P2PMessage(self.node_id, peer_node_id, MessageType.PROVISIONAL_ACCEPT, data)
        await hub.direct_send(self.node_id, peer_node_id, msg)
        
        # 2. Wait for peer's digital signature
        sign_req = P2PMessage(self.node_id, peer_node_id, MessageType.FINAL_APPROVAL_REQ, data)
        resp = await hub.direct_send(self.node_id, peer_node_id, sign_req)
        
        if resp and resp.msg_type == MessageType.DEAL_SIGNED:
            logging.info(f"Consensus Reached! Deal signed by {peer_node_id}")
            # Finalize and record to the Shared Ledger
            final_deal = {
                "farmer": self.node_id,
                "partner": peer_node_id,
                "crop": crop,
                "timestamp": datetime.now().isoformat(),
                "signatures": [msg.signature, resp.signature]
            }
            ledger_block = hub.record_signed_deal(final_deal)
            
            # Broadcast finalization to the network
            finish_msg = P2PMessage(self.node_id, "BROADCAST", MessageType.DEAL_FINALIZED, final_deal)
            await hub.broadcast(self.node_id, finish_msg)
            return ledger_block
            
        return {"status": "FAILED", "reason": "Peer did not sign"}

    def get_local_scenarios(self, crop: str):
        """Analyze gathered peer interests locally using AI."""
        interests = self.get_state(f"interests_{crop}") or []
        if not interests:
            return []

        prompt = f"As a Farmer AI agent, rank these buyer interests for my {crop}: {json.dumps(interests)}. " \
                 f"Output a JSON list of 3 scenarios with: type, estimated_price, score (0-100), summary, peer_node."
        
        ai_res = self.llm.generate(prompt)
        try:
            clean = ai_res.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except:
            scenarios = []
            for i in interests:
                peer_data = i['data']
                scenarios.append({
                    "peer_node": i['from_node'],
                    "type": peer_data.get("scenario_type", "direct-sale"),
                    "estimated_price": peer_data.get("price", 18),
                    "score": 85,
                    "summary": f"Decentralized match with {i['from_node']}"
                })
            return sorted(scenarios, key=lambda x: x['score'], reverse=True)
