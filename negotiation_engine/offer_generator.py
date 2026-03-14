import time


class OfferGenerator:

    def __init__(self):
        pass

    # --------------------------------------
    # Standardize Offer Structure
    # --------------------------------------

    def create_offer(self, agent_name, offer_type, price=None, quantity=None, message=""):

        offer = {
            "agent": agent_name,
            "type": offer_type,
            "price": price,
            "quantity": quantity,
            "message": message,
            "timestamp": time.time()
        }

        return offer

    # --------------------------------------
    # Generate Initial Farmer Offer
    # --------------------------------------

    def generate_farmer_offer(self, farmer):

        farmer_offer = farmer.make_offer()

        offer = self.create_offer(
            agent_name=farmer.name,
            offer_type="OFFER",
            price=farmer_offer.get("price"),
            quantity=farmer_offer.get("quantity"),
            message=farmer_offer.get("message")
        )

        return offer

    # --------------------------------------
    # Generate Buyer Offer
    # --------------------------------------

    def generate_buyer_offer(self, buyer, context):

        buyer_offer = buyer.make_offer(context)

        offer = self.create_offer(
            agent_name=buyer.name,
            offer_type=buyer_offer.get("type", "OFFER"),
            price=buyer_offer.get("price"),
            quantity=buyer_offer.get("quantity"),
            message=buyer_offer.get("message")
        )

        return offer

    # --------------------------------------
    # Generate Counter Offer
    # --------------------------------------

    def generate_counter_offer(self, agent, response):

        offer = self.create_offer(
            agent_name=agent.name,
            offer_type=response.get("type"),
            price=response.get("price"),
            quantity=response.get("quantity"),
            message=response.get("message")
        )

        return offer

    # --------------------------------------
    # Validate Offer
    # --------------------------------------

    def validate_offer(self, offer):

        required_fields = ["type"]

        for field in required_fields:
            if field not in offer:
                return False

        return True