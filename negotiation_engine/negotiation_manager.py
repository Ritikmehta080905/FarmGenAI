from negotiation_engine.offer_generator import OfferGenerator
from negotiation_engine.counter_offer_logic import CounterOfferLogic
from negotiation_engine.deal_evaluator import DealEvaluator
from negotiation_engine.negotiation_memory import NegotiationMemory


class NegotiationManager:

    def __init__(self, farmer, buyer, max_rounds=10):

        self.farmer = farmer
        self.buyer = buyer

        self.max_rounds = max_rounds

        # Engine modules
        self.offer_generator = OfferGenerator()
        self.counter_logic = CounterOfferLogic()
        self.deal_evaluator = DealEvaluator()
        self.memory = NegotiationMemory()

        # Conversation log
        self.log = []

    # ----------------------------------------
    # Start Negotiation
    # ----------------------------------------

    def start_negotiation(self):

        round_count = 0

        # Generate initial offer
        current_offer = self.offer_generator.generate_farmer_offer(self.farmer)

        self.log.append(current_offer["message"])
        self.memory.store_offer("Farmer", current_offer)

        # Negotiation loop
        while round_count < self.max_rounds:

            round_count += 1

            self.log.append(f"--- Round {round_count} ---")

            # --------------------------------
            # Buyer evaluates offer
            # --------------------------------

            buyer_response = self.buyer.respond_to_offer(current_offer)

            self.log.append(buyer_response["message"])
            self.memory.store_offer("Buyer", buyer_response)

            response_type = buyer_response["type"]

            # Check deal acceptance
            if self.deal_evaluator.is_accepted(response_type):

                self.memory.store_deal(buyer_response)

                self.log.append(
                    f"Deal finalized at ₹{buyer_response['price']}/kg "
                    f"for {buyer_response['quantity']}kg"
                )

                return True

            # Buyer rejects
            if response_type == "REJECT":

                self.log.append("Buyer rejected the deal.")
                return False

            # Buyer counter
            if response_type == "COUNTER":

                current_offer = self.counter_logic.process_counter_offer(
                    buyer_response
                )

            # --------------------------------
            # Farmer evaluates counter offer
            # --------------------------------

            farmer_response = self.farmer.respond_to_offer(current_offer)

            self.log.append(farmer_response["message"])
            self.memory.store_offer("Farmer", farmer_response)

            response_type = farmer_response["type"]

            if self.deal_evaluator.is_accepted(response_type):

                self.memory.store_deal(farmer_response)

                self.log.append(
                    f"Deal finalized at ₹{farmer_response['price']}/kg "
                    f"for {farmer_response['quantity']}kg"
                )

                return True

            if response_type == "REJECT":

                self.log.append("Farmer rejected the deal.")
                return False

            if response_type == "COUNTER":

                current_offer = self.counter_logic.process_counter_offer(
                    farmer_response
                )

        # Negotiation timeout
        self.log.append("Negotiation failed: maximum rounds reached.")
        return False