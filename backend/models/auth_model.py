from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict


class SignupRequest(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = "user@agri.com"
    password: str
    location: Optional[str] = "Pune"
    language: str = "Marathi"
    role: str = "FARMER"


class LoginRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str


class AuthResponse(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    location: str
    language: str
    role: Optional[str] = None
    verification_status: Optional[str] = "PENDING"
    preferences: Optional[Dict] = {}
    trust_score: float = 4.0
    token: Optional[str] = ""
    message: str


class VerificationRequest(BaseModel):
    user_id: str
    docs: List[str] # List of mock file names


class PreferenceRequest(BaseModel):
    user_id: Optional[str] = None
    preferences: Dict