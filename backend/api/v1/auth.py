from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import AsyncSessionLocal
from backend.repositories.user_repo import UserRepository
from backend.services.security import verify_password, create_access_token
from backend.models.auth_model import SignupRequest, LoginRequest
from pydantic import BaseModel

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/register", response_model=TokenResponse)
async def register(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    if await repo.get_by_email(request.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = await repo.create(request)
    token = create_access_token({"sub": user.id, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "role": user.role, "full_name": user.full_name}
    }

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_email(request.email)
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
        
    token = create_access_token({"sub": user.id, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "role": user.role, "full_name": user.full_name}
    }

@router.get("/me")
async def get_me(db: AsyncSession = Depends(get_db)):
    # This is a stub for /me. Ideally it uses dependency injection to extract token user
    return {"message": "Use token validation"}
