import json
import sqlite3
from fastapi import APIRouter, HTTPException
from backend.controllers.auth_controller import signup_controller, login_controller
from backend.models.auth_model import SignupRequest, LoginRequest, AuthResponse
from database.db import Database

router = APIRouter(tags=["Auth"])


@router.post("/signup", response_model=AuthResponse)
def signup(data: SignupRequest):
    result = signup_controller(data.dict())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest):
    result = login_controller(data.dict())
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    return result


@router.get("/me", response_model=AuthResponse)
def get_me(user_id: str):
    user = Database.users.get(user_id)
    if not user:
        # Check database if not in cache
        with sqlite3.connect("agrinegotiator.db") as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
            if row:
                user = dict(row)
                Database.users[user_id] = user
    
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    return {
        "user_id": user_id,
        "name": user["name"],
        "email": user["email"],
        "location": user["location"],
        "language": user.get("language", "Marathi"),
        "trust_score": user.get("trust_score", 4.0),
        "message": "User verified"
    }