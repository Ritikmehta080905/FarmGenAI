from ..services.negotiation_service import NegotiationService

class NegotiationController:
    def __init__(self):
        self.service = NegotiationService()

    def start_negotiation(self, farmer_id, buyer_id):
        return self.service.start_negotiation(farmer_id, buyer_id)

    def make_offer(self, negotiation_id, offer):
        return self.service.make_offer(negotiation_id, offer)

    def get_negotiation_status(self, negotiation_id):
        return self.service.get_negotiation_status(negotiation_id)
