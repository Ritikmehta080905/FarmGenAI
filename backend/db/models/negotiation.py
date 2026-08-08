from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Float, ForeignKey, JSON
from backend.db.session import Base
import uuid
from datetime import datetime

class Negotiation(Base):
    __tablename__ = "negotiations"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    farmer_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    buyer_id: Mapped[str] = mapped_column(String)
    produce_type: Mapped[str] = mapped_column(String)
    quantity: Mapped[float] = mapped_column(Float)
    target_price: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="pending")
    history: Mapped[dict] = mapped_column(JSON, default=list)
