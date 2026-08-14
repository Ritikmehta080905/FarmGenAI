from pydantic import BaseModel
from typing import List, Optional, Any, Dict


class HistoryItem(BaseModel):
    negotiation_id: Optional[str] = None
    crop: Optional[str] = None
    quantity: Optional[float] = None
    status: Optional[str] = None
    final_price: Optional[float] = None
    summary: Optional[str] = None
    type: Optional[str] = None
    id: Optional[str] = None
    role: Optional[str] = None
    price: Optional[float] = None
    actor_name: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[str] = None


class HistoryResponse(BaseModel):
    user_id: str
    history: List[Dict[str, Any]]