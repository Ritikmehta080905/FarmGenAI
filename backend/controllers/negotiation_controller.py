from ..services.negotiation_service import service

class NegotiationController:
    def __init__(self):
        self.service = service

    async def start_negotiation(self, payload, scenario="direct-sale", pre_id=None, live_event_callback=None):
        return await self.service.start_negotiation(
            payload,
            scenario=scenario,
            pre_id=pre_id,
            live_event_callback=live_event_callback,
        )

    async def get_agents(self):
        return await self.service.list_agents()

    async def get_negotiation_status(self, negotiation_id):
        return await self.service.get_negotiation_status(negotiation_id)
