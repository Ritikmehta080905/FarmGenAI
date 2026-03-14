from ..services.negotiation_service import service

class NegotiationController:
    def __init__(self):
        self.service = service

    def start_negotiation(self, payload, scenario="direct-sale", pre_id=None):
        return self.service.start_negotiation(payload, scenario=scenario, pre_id=pre_id)

    def get_agents(self):
        return self.service.list_agents()

    def get_negotiation_status(self, negotiation_id):
        return self.service.get_negotiation_status(negotiation_id)
