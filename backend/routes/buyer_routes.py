from fastapi import APIRouter
from ..controllers.buyer_controller import get_buyers_controller

router = APIRouter()

@router.get("/")
async def get_buyers():
    return {"buyers": get_buyers_controller()}
