from fastapi import APIRouter, HTTPException
from backend.controllers.auth_controller import signup_controller, login_controller
from backend.models.auth_model import SignupRequest, LoginRequest, AuthResponse

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
        raise HTTPException(status_code=401, detail="Not logged in")
    
    data = json.loads(user["data"])
    return {
        "user_id": user_id,
        "name": data["name"],
        "email": data["email"],
        "location": data["location"],
        "language": data.get("language", "Marathi"),
        "trust_score": data.get("trust_score", 4.0),
        "message": "User verified"
    }