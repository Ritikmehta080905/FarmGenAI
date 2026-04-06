from .base_node import BaseNode
from .p2p_protocol import MessageType, P2PMessage
import logging
import json

class BuyerNode(BaseNode):
    def __init__(self, node_id: str, buyer_name: str, preferred_crops: list):
        super().__init__(node_id, "buyer")
        self.buyer_name = buyer_name
        self.preferred_crops = preferred_crops
        self.save_state("preferences", {"crops": preferred_crops, "max_price": 25})

    async def handle_message(self, msg: P2PMessage) -> list:
        await super().handle_message(msg)
        
        responses = []
        if msg.msg_type == MessageType.SUPPLY_ANNOUNCE:
            crop = msg.data.get("crop")
            if crop in self.preferred_crops:
                logging.info(f"Buyer Node {self.node_id} analyzing {crop} announcement via AI...")
                
                # Autonomous AI decision on interest
                qty = msg.data.get("quantity", 0)
                min_p = msg.data.get("min_price", 0)
                
                prompt = f"Farmer offers {qty}kg of {crop} starting at Rs.{min_p}. High quality. Suggest a slightly better bid price to win the deal. Respond only with the number."
                bid_price = self.llm.generate(prompt) or str(min_p * 1.05)
                try:
                    bid_price = float(bid_price.strip())
                except:
                    bid_price = min_p * 1.05

                resp_data = {
                    "buyer_name": self.buyer_name,
                    "crop": crop,
                    "price": round(bid_price, 2),
                    "scenario_type": "direct-sale",
                    "status": "INTERESTED"
                }
                reply = P2PMessage(self.node_id, msg.from_node, MessageType.MATCH_INTEREST, resp_data)
                responses.append(reply)
                
        elif msg.msg_type == MessageType.FINAL_APPROVAL_REQ:
            # Local decision to sign the deal (Sovereignty)
            logging.info(f"Buyer Node {self.node_id} signing final deal for {msg.data.get('crop')}...")
            sign_resp = P2PMessage(self.node_id, msg.from_node, MessageType.DEAL_SIGNED, {"status": "SUCCESS"})
            responses.append(sign_resp)
            
        return responses
