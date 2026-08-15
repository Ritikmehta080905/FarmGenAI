from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    location: str
    language: str = "Marathi"
    role: str # Added for role-based testing


class LoginRequest(BaseModel):
    email: EmailStr
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
    message: str


class VerificationRequest(BaseModel):
    user_id: Optional[str] = None
    docs: List[str] # List of mock file names


class PreferenceRequest(BaseModel):
    user_id: Optional[str] = None
    preferences: Dict
