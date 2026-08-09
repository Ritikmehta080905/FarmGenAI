from backend.repositories.user_repository import UserRepository
from fastapi import APIRouter, HTTPException, Depends
from backend.controllers.auth_controller import signup_controller, login_controller
from backend.models.auth_model import SignupRequest, LoginRequest, AuthResponse, VerificationRequest, PreferenceRequest
from backend.services.security import get_current_user
from database.db import Database

router = APIRouter(tags=["Auth"])


@router.post("/signup", response_model=AuthResponse)
async def signup(data: SignupRequest):
    # Pass role to controller
    result = signup_controller(data.dict())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Store the role in the database for persistence
    user = await UserRepository.get_by_id(result["user_id"])
    if user:
        user["role"] = data.role
        await UserRepository.upsert(user)
        result["role"] = data.role
        
    return result


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest):
    result = login_controller(data.dict())
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    
    # Enrich with details from database
    user = await UserRepository.get_by_id(result["user_id"])
    if user:
        result["role"] = user.get("role")
        result["verification_status"] = user.get("verification_status", "PENDING")
        result["preferences"] = user.get("preferences", {})

    return result


@router.get("/me", response_model=AuthResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    user_id = current_user["sub"]
    user = await UserRepository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {
        "user_id": user_id,
        "name": user["name"],
        "email": user["email"],
        "location": user.get("location", ""),
        "language": user.get("language", "English"),
        "role": user.get("role"),
        "verification_status": user.get("verification_status", "PENDING"),
        "preferences": user.get("preferences", {}),
        "trust_score": user.get("trust_score", 4.0),
        "token": "",
        "message": "User verified"
    }


@router.post("/verify")
async def verify_user(request: VerificationRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["sub"]
    user = await UserRepository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user["verification_docs"] = request.docs
    user["verification_status"] = "PENDING"
    await UserRepository.upsert(user)
    return {"status": "success", "message": "Verification documents uploaded. Status: PENDING"}


@router.post("/preferences")
async def update_preferences(request: PreferenceRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["sub"]
    user = await UserRepository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Merge existing and new preferences
    current_prefs = user.get("preferences", {})
    current_prefs.update(request.preferences)
    user["preferences"] = current_prefs
    
    await UserRepository.upsert(user)
    return {"status": "success", "preferences": current_prefs}


@router.post("/location")
async def update_location(location: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["sub"]
    user = await UserRepository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user["location"] = location
    await UserRepository.upsert(user)
    return {"status": "success", "location": location}
