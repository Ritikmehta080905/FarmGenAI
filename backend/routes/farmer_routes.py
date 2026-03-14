from fastapi import APIRouter
from ..controllers.farmer_controller import get_farmers_controller, get_produce_controller

router = APIRouter()

@router.get("/farmers")
async def get_farmers():
    return {"farmers": get_farmers_controller()}


@router.get("/produce")
async def get_produce():
    return {"produce": get_produce_controller()}
