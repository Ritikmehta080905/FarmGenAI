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
        buyer=None,
        warehouse=None,
        compost=None,
        processor=None,
        animal_farm=None,
        offer_generator=None,
        memory=None,
        max_rounds=4,
        **kwargs
    ):

        # Agents
        self.farmer = farmer
        self.buyer = buyer
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

        event_bus.emit("offer_made", current_offer)

        for round_number in range(1, self.max_rounds + 1):

            self.logs.append(f"--- Round {round_number} ---")

            context = {
                "market_price": market_price,
                "round": round_number,
            }

            buyer_response = self.buyer.respond_to_offer(current_offer, context)
            buyer_price = buyer_response.get("price", farmer_price)

            self.logs.append(buyer_response["message"])
            self.memory.add_price("Buyer", buyer_price)
            self.memory.store_offer("Buyer", buyer_response)
            self.memory.store_event("offer", buyer_response)

            event_bus.emit("counter_offer", buyer_response)

            if buyer_response.get("type") == "ACCEPT":
                deal = {
                    "type": "ACCEPT",
                    "price": buyer_response.get("price", current_offer.get("price", market_price)),
                    "quantity": buyer_response.get("quantity", quantity),
                }
                self.logs.append(f"Deal reached at ₹{deal['price']}/kg for {deal['quantity']}kg")
                event_bus.emit("agreement", deal)
                return {
                    "state": "DEAL",
                    "summary": "Negotiation successful",
                    "deal": deal,
                    "logs": self.logs,
                    "price_series": self.memory.get_price_series(),
                    "next_action": "Transport crop",
                }

            if buyer_response.get("type") == "REJECT":
                self.logs.append("Buyer rejected the offer.")
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
            self.memory.store_offer("Farmer", farmer_response)
            self.memory.store_event("offer", farmer_response)

            event_bus.emit("counter_offer", farmer_response)

            if farmer_response.get("type") == "ACCEPT":
                deal = {
                    "type": "ACCEPT",
                    "price": farmer_response.get("price", current_offer.get("price", market_price)),
                    "quantity": farmer_response.get("quantity", quantity),
                }
                self.logs.append(f"Deal reached at ₹{deal['price']}/kg for {deal['quantity']}kg")
                event_bus.emit("agreement", deal)
                return {
                    "state": "DEAL",
                    "summary": "Negotiation successful",
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

        return self._handle_escalation(market_price, quantity)

    # ------------------------------------------------
    # Escalation
    # ------------------------------------------------

    def _handle_escalation(self, market_price, quantity):

        if self.warehouse and hasattr(self.warehouse, "respond_to_offer"):

            response = self.warehouse.respond_to_offer({
                "quantity": quantity,
                "crop": getattr(self.farmer, "crop", "produce"),
                "type": "STORAGE_REQUEST",
            })

            event_bus.emit("storage", response)

            return {
                "state": "ESCALATED_STORAGE",
                "summary": "Crop stored in warehouse",
                "deal": response,
                "logs": self.logs,
                "price_series": self.memory.get_price_series(),
                "next_action": "Wait for price recovery"
            }

        return {
            "state": "FAILED",
            "summary": "Negotiation failed",
            "logs": self.logs,
            "price_series": self.memory.get_price_series()
        }