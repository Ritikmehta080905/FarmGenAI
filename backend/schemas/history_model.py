from pydantic import BaseModel
from typing import List, Optional


class HistoryItem(BaseModel):
    negotiation_id: str
    crop: Optional[str] = None
    quantity: Optional[float] = None
    status: Optional[str] = None
    final_price: Optional[float] = None
    summary: Optional[str] = None


class HistoryResponse(BaseModel):
    user_id: str
    history: List[HistoryItem]
