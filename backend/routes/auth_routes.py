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