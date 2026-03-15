def build_offer_event(round_number, agent, offer):
    """
    Build a structured event representing a negotiation offer.
    """

    return {
        "round": round_number,
        "agent": agent,
        "type": offer.get("type"),
        "price": offer.get("price"),
        "quantity": offer.get("quantity"),
        "message": offer.get("message")
    }