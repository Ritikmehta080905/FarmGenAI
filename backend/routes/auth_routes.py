import json
import sqlite3
from fastapi import APIRouter, HTTPException
from backend.controllers.auth_controller import signup_controller, login_controller
from backend.models.auth_model import SignupRequest, LoginRequest, AuthResponse, VerificationRequest, PreferenceRequest
from database.db import Database

router = APIRouter(tags=["Auth"])


@router.post("/signup", response_model=AuthResponse)
def signup(data: SignupRequest):
    # Pass role to controller
    result = signup_controller(data.dict())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Store the role in the database for persistence
    user = Database.get_user(result["user_id"])
    if user:
        user["role"] = data.role
        Database.upsert_user(user)
        result["role"] = data.role
        
    return result


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest):
    result = login_controller(data.dict())
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    
    # Enrich with details from database
    user = Database.get_user(result["user_id"])
    if user:
        result["role"] = user.get("role")
        result["verification_status"] = user.get("verification_status", "PENDING")
        result["preferences"] = user.get("preferences", {})

    return result


@router.get("/me", response_model=AuthResponse)
def get_me(user_id: str):
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
        "message": "User verified"
    }


@router.post("/verify")
def verify_user(request: VerificationRequest):
    user = Database.get_user(request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user["verification_docs"] = request.docs
    user["verification_status"] = "PENDING"
    Database.upsert_user(user)
    return {"status": "success", "message": "Verification documents uploaded. Status: PENDING"}


@router.post("/preferences")
def update_preferences(request: PreferenceRequest):
    user = Database.get_user(request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Merge existing and new preferences
    current_prefs = user.get("preferences", {})
    current_prefs.update(request.preferences)
    user["preferences"] = current_prefs
    
    Database.upsert_user(user)
    return {"status": "success", "preferences": current_prefs}


@router.post("/location")
def update_location(user_id: str, location: str):
    user = Database.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user["location"] = location
    Database.upsert_user(user)
    return {"status": "success", "location": location}