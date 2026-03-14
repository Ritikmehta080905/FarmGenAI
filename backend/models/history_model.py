from pydantic import BaseModel
from typing import List, Optional


class HistoryItem(BaseModel):
    negotiation_id: str
    crop: str
    quantity: float
    status: str
    final_price: Optional[float] = None
    summary: str


class HistoryResponse(BaseModel):
    user_id: str
    history: List[HistoryItem]