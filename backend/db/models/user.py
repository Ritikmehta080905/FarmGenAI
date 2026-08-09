from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean
from backend.db.session import Base
import uuid

class User(Base):
    __tablename__ = "v1_users"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, default="farmer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
