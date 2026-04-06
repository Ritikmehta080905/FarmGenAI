from negotiation_engine.offer_generator import OfferGenerator
from shared.event_bus import event_bus
import time

# ------------------------------------------------
# Safe Memory Class
# ------------------------------------------------

class SafeMemory:
    def __init__(self):
        self.price_series = []
        self.offers = []
        self.events = []

    def store_offer(self, agent, offer):
        self.offers.append({"agent": agent, "offer": offer})

    def get_offers(self):
        return self.offers

    def store_event(self, event_type, payload):
        self.events.append({"type": event_type, "payload": payload})

    def get_events(self):
        return self.events

    def add_price(self, agent, price):
        self.price_series.append({"agent": agent, "price": price})

    def get_price_series(self):
        return self.price_series


# ------------------------------------------------
# Negotiation Manager (Full Supply Chain Optimizer)
# ------------------------------------------------

class NegotiationManager:
    def __init__(
        self,
        farmer=None,
        buyers=None,
        warehouse=None,
        compost=None,
        processor=None,
        transporter=None,
        max_rounds=5,
        live_event_callback=None,
        **kwargs
    ):
        self.farmer = farmer
        self.buyers = buyers if isinstance(buyers, list) else []
        self.warehouse = warehouse
        self.compost = compost
        self.processor = processor
        self.transporter = transporter

        self.offer_generator = OfferGenerator()
        self.memory = SafeMemory()
        self.max_rounds = max_rounds
        self.logs = []
        self.live_event_callback = live_event_callback

    def _emit_live(self, event_type, data):
        event_bus.emit(event_type, data)
        if self.live_event_callback:
            try:
                self.live_event_callback({"type": event_type, "data": data})
            except:
                pass

    # ------------------------------------------------
    # Strategic Negotiation Start
    # ------------------------------------------------

    def start_negotiation(self, market_price: float, quantity: float = 500, **kwargs):
        self.logs.append("🔍 PHASE 1: Multi-Agent Marketplace Scan & Bid Invitation")
        self._emit_live("status_update", {"message": "Farmer calling for strategic bids from all networks..."})
        
        # Invite all potential buyers to 'Think'
        all_potential_deals = []
        for buyer in self.buyers:
            self.logs.append(f"📡 {buyer.name} is analyzing the opportunity...")
            ctx = {"market_price": market_price, "quantity": quantity, "initial": True}
            bid = buyer.make_offer(ctx)
            
            # Integrated Logistics Check
            distance = 50 
            transport_cost = 0
            if self.transporter:
                transport_cost = self.transporter.calculate_transport_cost(quantity, distance)
                
            net_profit = (bid["price"] * quantity) - transport_cost
            all_potential_deals.append({
                "buyer": buyer,
                "bid": bid,
                "net_profit": net_profit,
                "transport_cost": transport_cost
            })

        # Multi-Path Optimization logic
        all_potential_deals.sort(key=lambda x: x["net_profit"], reverse=True)
        top_paths = all_potential_deals[:3]

        self.logs.append(f"🤖 FARMER ANALYSIS: Evaluated {len(all_potential_deals)} paths. Focusing on most profitable candidates.")
        
        # 🔀 SPLIT ALLOCATION & PARTIAL FULFILLMENT (Phase E Test cases)
        remaining_qty = float(quantity)
        final_partnerships = []
        
        for path in top_paths:
            if remaining_qty <= 0: break
            
            buyer = path["buyer"]
            # Negotiate for what they want or what we have left
            alloc_qty = min(remaining_qty, buyer.max_quantity)
            self.logs.append(f"🤝 Negotiating {alloc_qty}kg chunk with: {buyer.name}")
            
            current_offer = self.offer_generator.generate_farmer_offer(self.farmer, market_price)
            farmer_price = current_offer["price"]
            self.memory.add_price("Farmer", farmer_price)

            deal_for_this_partner = None
            for round_num in range(1, self.max_rounds + 1):
                ctx = {"market_price": market_price, "round": round_num, "quantity": alloc_qty}

                # Buyer Turn
                buyer_resp = buyer.respond_to_offer(current_offer, ctx)
                buyer_price = buyer_resp.get("price", farmer_price)
                self.memory.add_price(buyer.name, buyer_price)
                self.logs.append(f"[{buyer.name}] {buyer_resp.get('message', '')}")
                self._emit_live("counter_offer", buyer_resp)
                
                if buyer_resp.get("type") == "ACCEPT":
                    deal_for_this_partner = {
                        "buyer_name": buyer.name,
                        "price": buyer_resp["price"],
                        "quantity": alloc_qty,
                        "transport_partner": self.transporter.name if self.transporter else "Local-Self"
                    }
                    break
                if buyer_resp.get("type") == "REJECT": break
                
                # Farmer Turn
                current_offer = {"type": "OFFER", "price": buyer_resp.get("price", farmer_price), "quantity": alloc_qty}
                farmer_resp = self.farmer.respond_to_offer(current_offer, ctx)
                farmer_price = farmer_resp.get("price", farmer_price)
                self.memory.add_price("Farmer", farmer_price)
                self.logs.append(f"[Farmer] {farmer_resp.get('message', '')}")
                self._emit_live("counter_offer", farmer_resp)
                
                if farmer_resp.get("type") == "ACCEPT":
                    deal_for_this_partner = {
                        "buyer_name": buyer.name,
                        "price": farmer_resp["price"],
                        "quantity": alloc_qty,
                        "transport_partner": self.transporter.name if self.transporter else "Local-Self"
                    }
                    break
                
                current_offer = {"type": "OFFER", "price": farmer_price, "quantity": alloc_qty}

            if deal_for_this_partner:
                self.logs.append(f"✅ CHUNK SECURED: {deal_for_this_partner['buyer_name']} at ₹{deal_for_this_partner['price']}/kg")
                final_partnerships.append(deal_for_this_partner)
                remaining_qty -= alloc_qty
                self._emit_live("agreement", deal_for_this_partner)

        if final_partnerships:
            remaining_text = f" (Remaining {remaining_qty}kg to fallbacks)" if remaining_qty > 0 else ""
            return {
                "state": "DEAL",
                "summary": f"Split deal across {len(final_partnerships)} buyers.{remaining_text}",
                "partnerships": final_partnerships,
                "remaining_quantity": remaining_qty,
                "logs": self.logs,
                "price_series": self.memory.get_price_series(),
                "next_action": "Logistics Dispatch" if remaining_qty == 0 else "Trigger Fallback"
            }

        # If zero buyers accepted, handle fallback for total qty
        return self._handle_escalation(market_price, quantity)

    def _handle_escalation(self, market_price, quantity):
        self.logs.append("⚠️ Market saturation detected. Escalating to Supply Chain fallbacks...")
        
        if self.warehouse:
            self.logs.append(f"🏗️ Analyzing Warehouse Storage Strategy at {self.warehouse.name}...")
            response = self.warehouse.respond_to_offer({"quantity": quantity, "type": "STORAGE"})
            if response.get("type") != "REJECT":
                self._emit_live("storage", response)
                return {"state": "ESCALATED_STORAGE", "deal": response, "logs": self.logs, "price_series": self.memory.get_price_series()}

        if self.processor:
            self.logs.append(f"⚙️ Analyzing Alternative Value-Added Processing at {self.processor.name}...")
            response = self.processor.respond_to_offer({"price": market_price * 0.8, "quantity": quantity})
            if response.get("type") == "ACCEPT_PROCESSING":
                 self._emit_live("processing", response)
                 return {"state": "ESCALATED_PROCESSING", "deal": response, "logs": self.logs, "price_series": self.memory.get_price_series()}

        if self.compost:
            self.logs.append("♻️ Zero-Waste Fallback: Engaging Ecological Recovery Agents...")
            response = self.compost.respond_to_offer({"quantity": quantity})
            self._emit_live("compost", response)
            return {"state": "ESCALATED_COMPOST", "deal": response, "logs": self.logs, "price_series": self.memory.get_price_series()}

        return {"state": "FAILED", "logs": self.logs, "price_series": self.memory.get_price_series()}