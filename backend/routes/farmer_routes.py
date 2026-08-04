from fastapi import APIRouter, Depends
from ..controllers.farmer_controller import get_farmers_controller, get_produce_controller
from backend.services.security import get_current_user

router = APIRouter()

@router.get("/farmers")
async def get_farmers(current_user: dict = Depends(get_current_user)):
    return {"farmers": get_farmers_controller()}


@router.get("/produce")
async def get_produce(current_user: dict = Depends(get_current_user)):
    return {"produce": get_produce_controller()}
