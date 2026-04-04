from pydantic import BaseModel


class RoleOfferCreate(BaseModel):
    user_id: str | None = None
    role: str
    actor_name: str
    crop: str
    quantity: float
    offered_price: float | None = None
    location: str
    notes: str = ""


class RoleOfferResponse(BaseModel):
    id: str
    user_id: str | None = None
    role: str
    actor_name: str
    crop: str
    quantity: float
    offered_price: float | None = None
    location: str
    notes: str = ""
    status: str
    created_at: str
