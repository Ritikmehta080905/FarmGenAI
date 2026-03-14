from pydantic import BaseModel


class ProduceCreate(BaseModel):
    user_id: str | None = None
    farmer_name: str = "Unknown Farmer"
    crop: str
    quantity: float
    min_price: float
    shelf_life: int
    location: str
    quality: str = "A"
    language: str = "Marathi"


class ProduceResponse(BaseModel):
    id: str
    farmer_name: str
    crop: str
    quantity: float
    min_price: float
    shelf_life: int
    location: str
    quality: str
    language: str
    status: str