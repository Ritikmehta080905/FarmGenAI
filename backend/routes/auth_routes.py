from fastapi import APIRouter, HTTPException, Depends
from backend.controllers.auth_controller import signup_controller, login_controller
from backend.models.auth_model import SignupRequest, LoginRequest, AuthResponse, VerificationRequest, PreferenceRequest
from backend.services.security import get_current_user
from database.db import Database

router = APIRouter(tags=["Auth"])


@router.post("/signup", response_model=AuthResponse)
@router.post("/register", response_model=AuthResponse)
async def signup(data: SignupRequest):
    # Pass role to controller
    result = await signup_controller(data.dict())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Store the role in the database for persistence
    user = await Database.get_user_async(result["user_id"])
    if user:
        user["role"] = data.role
        await Database.upsert_user_async(user)
        result["role"] = data.role
        
    return result


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest):
    result = await login_controller(data.dict())
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    
    # Enrich with details from database
    user = await Database.get_user_async(result["user_id"])
    if user:
        result["role"] = user.get("role")
        result["verification_status"] = user.get("verification_status", "PENDING")
        result["preferences"] = user.get("preferences", {})

    return result


@router.get("/me", response_model=AuthResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    user_id = current_user["sub"]
    user = Database.get_user(user_id)
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
def verify_user(request: VerificationRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["sub"]
    user = Database.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user["verification_docs"] = request.docs
    user["verification_status"] = "PENDING"
    Database.upsert_user(user)
    return {"status": "success", "message": "Verification documents uploaded. Status: PENDING"}


@router.post("/preferences")
async def update_preferences(payload: dict, current_user: dict = Depends(get_current_user)):
    user_id = current_user["sub"]
    user = await Database.get_user_async(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Extract preferences whether nested under 'preferences' key or provided flat
    new_prefs = payload.get("preferences") if isinstance(payload.get("preferences"), dict) else payload
    # Remove metadata keys if present in flat payload
    new_prefs = {k: v for k, v in new_prefs.items() if k not in ["user_id", "token"]}

    current_prefs = user.get("preferences", {}) or {}
    current_prefs.update(new_prefs)
    user["preferences"] = current_prefs
    
    await Database.upsert_user_async(user)
    return {"status": "success", "preferences": current_prefs}


@router.post("/location")
def update_location(location: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["sub"]
    user = Database.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user["location"] = location
    Database.upsert_user(user)
    return {"status": "success", "location": location}