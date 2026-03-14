from pydantic import BaseModel


class WarehouseResponse(BaseModel):
    name: str
    capacity: float