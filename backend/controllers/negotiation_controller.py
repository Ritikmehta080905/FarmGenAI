from backend.services.negotiation_service import start_negotiation, get_negotiation_status


def start_negotiation_controller(data: dict):
    return start_negotiation(data)


def negotiation_status_controller(negotiation_id: str):
    return get_negotiation_status(negotiation_id)