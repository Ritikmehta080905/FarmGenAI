from fastapi import APIRouter
from typing import List
from backend.controllers.buyer_controller import get_buyers_controller
from backend.models.buyer_model import BuyerResponse

router = APIRouter(tags=["Buyers"])


@router.get("/buyers", response_model=List[BuyerResponse])
def buyers():
    return get_buyers_controller()