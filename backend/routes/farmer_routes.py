from fastapi import APIRouter
from typing import List
from backend.controllers.farmer_controller import get_farmers_controller, get_produce_controller
from backend.models.farmer_model import FarmerResponse
from backend.models.produce_model import ProduceResponse

router = APIRouter(tags=["Farmers"])


@router.get("/farmers", response_model=List[FarmerResponse])
def farmers():
    return get_farmers_controller()


@router.get("/produce", response_model=List[ProduceResponse])
def produce():
    return get_produce_controller()