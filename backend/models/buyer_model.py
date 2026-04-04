from pydantic import BaseModel


class BuyerResponse(BaseModel):
    name: str
    crop: str


class BuyerOfferCreate(BaseModel):
    user_id: str | None = None
    buyer_name: str
    crop: str
    offered_price: float
    quantity: float
    location: str
    strategy: str = "Direct procurement offer"


class BuyerOfferResponse(BaseModel):
    id: str
    buyer_name: str
    crop: str
    offered_price: float
    quantity: float
    location: str
    strategy: str
    status: str