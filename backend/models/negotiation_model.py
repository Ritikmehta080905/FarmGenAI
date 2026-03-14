from pydantic import BaseModel
from typing import List, Optional


class Offer(BaseModel):
    round: int
    agent: str
    price: float
    decision: str


class StartNegotiationRequest(BaseModel):
    user_id: str | None = None
    farmer_name: str = "Unknown Farmer"
    crop: str
    quantity: float
    min_price: float
    shelf_life: int
    location: str
    quality: str = "A"
    language: str = "Marathi"


class NegotiationResponse(BaseModel):
    negotiation_id: str
    status: str
    offers: List[Offer]


class NegotiationStatusResponse(BaseModel):
    negotiation_id: str
    status: str
    offers: List[Offer]
    summary: Optional[str] = None
    final_price: Optional[float] = None
    next_action: Optional[str] = None


class SimulationRequest(BaseModel):
    user_id: str | None = None
    scenario: str