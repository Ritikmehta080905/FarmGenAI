from fastapi import APIRouter
from typing import List
from backend.services.negotiation_service import list_warehouses
from backend.models.warehouse_model import WarehouseResponse

router = APIRouter(tags=["Warehouses"])


@router.get("/warehouses", response_model=List[WarehouseResponse])
def warehouses():
    return list_warehouses()