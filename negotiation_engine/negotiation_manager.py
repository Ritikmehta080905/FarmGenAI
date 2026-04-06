from negotiation_engine.offer_generator import OfferGenerator
from shared.event_bus import event_bus


# ------------------------------------------------
# Safe Memory Class
# ------------------------------------------------

class SafeMemory:

    def __init__(self):
        self.price_series = []
        self.offers = []
        self.events = []

    def store_offer(self, agent, offer):
        self.offers.append({
            "agent": agent,
            "offer": offer
        })

    def get_offers(self):
        return self.offers

    def store_event(self, event_type, payload):
        self.events.append({"type": event_type, "payload": payload})

    def get_events(self):
        return self.events

    def add_price(self, agent, price):
        self.price_series.append({
            "agent": agent,
            "price": price
        })

    def get_price_series(self):
        return self.price_series


# ------------------------------------------------
# Negotiation Manager
# ------------------------------------------------

class NegotiationManager:

    def __init__(
        self,
        farmer=None,
        buyers=None,
        buyer=None,
        warehouse=None,
        compost=None,
        processor=None,
        animal_farm=None,
        offer_generator=None,
        memory=None,
        max_rounds=4,
        live_event_callback=None,
        **kwargs
    ):

        # Agents
        self.farmer = farmer
        # Handle both plural and singular for compatibility
        self.buyers = buyers if isinstance(buyers, list) else ([buyer] if buyer else [])
        self.buyer = self.buyers[0] if self.buyers else None
        self.warehouse = warehouse
        self.compost = compost
        self.processor = processor
        self.animal_farm = animal_farm

        # Utilities
        self.offer_generator = offer_generator or OfferGenerator()
        self.memory = memory or SafeMemory()

        # Settings
        self.max_rounds = max_rounds

        # Logs
        self.logs = []
        self.log = self.logs
        self.live_event_callback = live_event_callback

    def _emit_live(self, event_type, data):
        event_bus.emit(event_type, data)
        if self.live_event_callback:
            try:
                self.live_event_callback({"type": event_type, "data": data})
            except Exception:
                # Live streaming is best-effort and should not break negotiation flow.
                pass

    # ------------------------------------------------
    # Negotiation Start
    # ------------------------------------------------

    def start_negotiation(self, market_price, quantity=500, **kwargs):

        current_offer = self.offer_generator.generate_farmer_offer(
            self.farmer,
            market_price=market_price,
        )

        quantity = current_offer.get("quantity", quantity)
        farmer_price = current_offer.get("price", market_price)

        self.logs.append(current_offer["message"])
        self.memory.add_price("Farmer", farmer_price)
        self.memory.store_offer("Farmer", current_offer)
        self.memory.store_event("offer", current_offer)

        self._emit_live("offer_made", current_offer)

        # Standard B2B/B2C Negotiation Loop (Direct Sales)
        for buyer in self.buyers:
            self.buyer = buyer
            self.logs.append(f"📡 Negotiating with Buyer: {buyer.name}")
            
            for round_number in range(1, self.max_rounds + 1):
                self.logs.append(f"--- {buyer.name} Round {round_number} ---")
                
                context = {
                    "market_price": market_price,
                    "round": round_number,
                    "crop": getattr(self.farmer, "crop", "produce"),
                    "quantity": quantity
                }
                
                buyer_response = self.buyer.respond_to_offer(current_offer, context)
                buyer_price = buyer_response.get("price", farmer_price)

                self.logs.append(buyer_response["message"])
                self.memory.add_price(buyer.name, buyer_price)
                self.memory.store_offer(buyer.name, buyer_response)
                self._emit_live("counter_offer", buyer_response)

                if buyer_response.get("type") == "ACCEPT":
                    deal = {
                        "type": "ACCEPT",
                        "price": buyer_response.get("price", current_offer.get("price", market_price)),
                        "quantity": buyer_response.get("quantity", quantity),
                        "buyer_name": buyer.name
                    }
                    self.logs.append(f"✅ Deal reached with {buyer.name} at ₹{deal['price']}/kg")
                    self._emit_live("agreement", deal)
                    return {
                        "state": "DEAL",
                        "summary": f"Negotiation successful with {buyer.name}",
                        "deal": deal,
                        "logs": self.logs,
                        "price_series": self.memory.get_price_series(),
                        "next_action": "Transport crop",
                    }

                if buyer_response.get("type") == "REJECT":
                    self.logs.append(f"❌ {buyer.name} rejected the offer permanently.")
                    break

                current_offer = {
                    "type": "OFFER",
                    "price": buyer_response.get("price", current_offer.get("price", market_price)),
                    "quantity": buyer_response.get("quantity", quantity),
                    "message": buyer_response.get("message", "Buyer countered."),
                }

                farmer_response = self.farmer.respond_to_offer(current_offer, context)
                farmer_price = farmer_response.get("price", farmer_price)

                self.logs.append(farmer_response["message"])
                self.memory.add_price("Farmer", farmer_price)
                self._emit_live("counter_offer", farmer_response)

                if farmer_response.get("type") == "ACCEPT":
                    deal = {
                        "type": "ACCEPT",
                        "price": farmer_response.get("price", current_offer.get("price", market_price)),
                        "quantity": farmer_response.get("quantity", quantity),
                        "buyer_name": buyer.name
                    }
                    self.logs.append(f"✅ Deal reached with {buyer.name} at ₹{deal['price']}/kg")
                    self._emit_live("agreement", deal)
                    return {
                        "state": "DEAL",
                        "summary": f"Negotiation successful with {buyer.name}",
                        "deal": deal,
                        "logs": self.logs,
                        "price_series": self.memory.get_price_series(),
                        "next_action": "Transport crop",
                    }

                if farmer_response.get("type") == "REJECT":
                    self.logs.append("Farmer rejected the offer.")
                    break

                current_offer = {
                    "type": "OFFER",
                    "price": farmer_response.get("price", farmer_price),
                    "quantity": farmer_response.get("quantity", quantity),
                    "message": farmer_response.get("message", "Farmer countered."),
                }
            
            # Loop ends for this buyer, continue to next if no deal reached
            self.logs.append(f"Moving to next available buyer...")

        return self._handle_escalation(market_price, quantity)

    # ------------------------------------------------
    # Escalation
    # ------------------------------------------------

    def _handle_escalation(self, market_price, quantity):
        self.logs.append("⚠️ No direct market deals found. Escalating to Supply Chain fallbacks...")
        crop = getattr(self.farmer, "crop", "produce")

        # 1. Try Warehouse Storage
        if self.warehouse:
            self.logs.append(f"🏗️ Attempting escalation to Warehouse: {self.warehouse.name}")
            response = self.warehouse.respond_to_offer({
                "quantity": quantity,
                "crop": crop,
                "type": "STORAGE_REQUEST",
            })
            if response.get("type") != "REJECT":
                self._emit_live("storage", response)
                return {
                    "state": "ESCALATED_STORAGE",
                    "summary": f"Crop securely stored at {self.warehouse.name} pending price recovery",
                    "deal": response,
                    "logs": self.logs,
                    "price_series": self.memory.get_price_series(),
                    "next_action": "Wait for price recovery"
                }

        # 2. Try Industrial Processor fallback
        if self.processor:
            self.logs.append(f"⚙️ Attempting escalation to Industrial Processor: {self.processor.name}")
            response = self.processor.respond_to_offer({
                "price": market_price * 0.8, # Accept lower price for industrial use
                "quantity": quantity,
                "crop": crop,
                "type": "OFFER"
            })
            if response.get("type") == "ACCEPT":
                self._emit_live("processing", response)
                return {
                    "state": "ESCALATED_PROCESSING",
                    "summary": f"Sold to industrial processor {self.processor.name} for value-added conversion",
                    "deal": response,
                    "logs": self.logs,
                    "price_series": self.memory.get_price_series(),
                    "next_action": "Process for juice/ketchup"
                }

        # 3. Try Compost/Waste Management fallback
        if self.compost:
            self.logs.append(f"♻️ Attempting escalation to Compost/Eco-Farm: {self.compost.name}")
            response = self.compost.respond_to_offer({
                "quantity": quantity,
                "crop": crop,
                "type": "WASTE_COLLECTION"
            })
            self._emit_live("compost", response)
            return {
                "state": "ESCALATED_COMPOST",
                "summary": f"Zero-waste fallback: Dispatched to {self.compost.name} for organic composting",
                "deal": response,
                "logs": self.logs,
                "price_series": self.memory.get_price_series(),
                "next_action": "Optimize for bio-fertilizer"
            }

        return {
            "state": "FAILED",
            "summary": "Supply chain exhausted: crop currently unmarketable",
            "logs": self.logs,
            "price_series": self.memory.get_price_series()
        }