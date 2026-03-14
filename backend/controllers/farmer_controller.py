from ..services.negotiation_service import list_farmers, list_produce


def get_farmers_controller():
    return list_farmers()


def get_produce_controller():
    return list_produce()