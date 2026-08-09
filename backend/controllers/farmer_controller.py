from ..services.negotiation_service import list_farmers, list_produce


async def get_farmers_controller():
    return list_farmers()


async def get_produce_controller():
    return list_produce()