from backend.services.negotiation_service import create_buyer_offer, list_buyer_offers, list_buyers


async def get_buyers_controller():
    return list_buyers()


async def get_buyer_offers_controller(user_id: str | None = None):
    return list_buyer_offers(user_id=user_id)


async def create_buyer_offer_controller(payload: dict):
    return create_buyer_offer(payload)