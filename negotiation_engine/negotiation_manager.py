# negotiation_engine/negotiation_manager.py
from negotiation_engine.offer_generator import OfferGenerator
from negotiation_engine.counter_offer_logic import CounterOfferLogic
from negotiation_engine.deal_evaluator import DealEvaluator
from negotiation_engine.negotiation_memory import NegotiationMemory
from negotiation_engine.negotiation_protocol import (
    NegotiationState,
    build_offer_event,
    build_terminal_result,
)

class NegotiationManager:

    def __init__(self, farmer, buyer, warehouse=None, processor=None, compost=None, max_rounds=10):

        self.farmer = farmer
        self.buyer = buyer
        self.warehouse = warehouse
        self.processor = processor
        self.compost = compost
        self.max_rounds = max_rounds

        self.offer_generator = OfferGenerator()
        self.counter_logic = CounterOfferLogic()
        self.deal_evaluator = DealEvaluator()
        self.memory = NegotiationMemory()

        self.log = []
        self.state = NegotiationState.OPEN

    # ----------------------------------------
    # Start Negotiation
    # ----------------------------------------
    def start_negotiation(self, market_price=None, scenario="direct-sale"):

        round_count = 0

        current_offer = self.offer_generator.generate_farmer_offer(self.farmer)
        self.log.append(current_offer["message"])
        self.memory.store_offer("Farmer", current_offer)
        self.memory.store_event("offer", build_offer_event(0, "Farmer", current_offer))

        context = {"market_price": market_price if market_price else current_offer["price"]}

        while round_count < self.max_rounds:
            round_count += 1
            self.log.append(f"--- Round {round_count} ---")

            # Buyer evaluates
            buyer_response = self.buyer.respond_to_offer(current_offer, context)
            self.log.append(buyer_response["message"])
            self.memory.store_offer("Buyer", buyer_response)
            self.memory.store_event("offer", build_offer_event(round_count, "Buyer", buyer_response))

            if self.deal_evaluator.is_accepted(buyer_response["type"]):
                self.memory.store_deal(buyer_response)
                self.state = NegotiationState.DEAL
                self.log.append(
                    f"Deal finalized at ₹{buyer_response['price']}/kg for {buyer_response['quantity']}kg"
                )
                return build_terminal_result(
                    state=self.state,
                    summary="Direct sale accepted by buyer",
                    deal=buyer_response,
                    next_action="Assign transport"
                )

            if buyer_response["type"] == "REJECT":
                self.log.append("Buyer rejected the deal.")
                break

            if buyer_response["type"] == "COUNTER":
                current_offer = self.counter_logic.process_counter_offer(buyer_response)
                self.state = NegotiationState.COUNTERING

            # Farmer evaluates
            farmer_response = self.farmer.respond_to_offer(current_offer, context)
            self.log.append(farmer_response["message"])
            self.memory.store_offer("Farmer", farmer_response)
            self.memory.store_event("offer", build_offer_event(round_count, "Farmer", farmer_response))

            if self.deal_evaluator.is_accepted(farmer_response["type"]):
                self.memory.store_deal(farmer_response)
                self.state = NegotiationState.DEAL
                self.log.append(
                    f"Deal finalized at ₹{farmer_response['price']}/kg for {farmer_response['quantity']}kg"
                )
                return build_terminal_result(
                    state=self.state,
                    summary="Direct sale accepted by farmer",
                    deal=farmer_response,
                    next_action="Assign transport"
                )

            if farmer_response["type"] == "REJECT":
                self.log.append("Farmer rejected the deal.")
                break

            if farmer_response["type"] == "COUNTER":
                current_offer = self.counter_logic.process_counter_offer(farmer_response)
                self.state = NegotiationState.COUNTERING

        escalation_result = self._handle_escalation(scenario=scenario, current_offer=current_offer)
        if escalation_result:
            return escalation_result

        self.state = NegotiationState.FAILED
        self.log.append("Negotiation failed: maximum rounds reached.")
        return build_terminal_result(
            state=self.state,
            summary="Negotiation failed after all rounds and fallbacks",
            deal=None,
            next_action="Retry with updated market context"
        )

    def _handle_escalation(self, scenario, current_offer):
        quantity = current_offer.get("quantity", 0)

        if scenario == "storage" and self.warehouse:
            storage_response = self.warehouse.respond_to_offer({"quantity": quantity, "crop": self.farmer.crop})
            self.log.append(storage_response["message"])
            self.memory.store_event("storage", storage_response)
            if storage_response["type"] == "ACCEPT_STORAGE":
                self.state = NegotiationState.ESCALATED_STORAGE
                return build_terminal_result(
                    state=self.state,
                    summary="Produce moved to warehouse for delayed sale",
                    deal={
                        "type": "STORE",
                        "price": 0,
                        "quantity": quantity,
                        "cost": storage_response["cost"]
                    },
                    next_action="Run next market cycle"
                )

        if scenario == "processing" and self.processor:
            processor_response = self.processor.respond_to_offer(current_offer)
            self.log.append(processor_response["message"])
            self.memory.store_event("processing", processor_response)
            if processor_response["type"] in {"ACCEPT", "COUNTER"}:
                self.state = NegotiationState.ESCALATED_PROCESSING
                return build_terminal_result(
                    state=self.state,
                    summary="Escalated to processor market",
                    deal=processor_response,
                    next_action="Schedule processing transport"
                )

        # Near spoilage or no alternate path -> compost fallback.
        if self.compost:
            compost_response = self.compost.respond_to_offer(current_offer)
            self.log.append(compost_response["message"])
            self.memory.store_event("compost", compost_response)
            if compost_response["type"] in {"ACCEPT", "COUNTER"}:
                self.state = NegotiationState.ESCALATED_COMPOST
                return build_terminal_result(
                    state=self.state,
                    summary="Fallback sale through compost channel",
                    deal=compost_response,
                    next_action="Close spoilage risk"
                )

        return None