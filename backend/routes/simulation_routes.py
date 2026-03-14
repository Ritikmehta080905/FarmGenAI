from fastapi import APIRouter

router = APIRouter()

@router.post("/run")
async def run_simulation():
    return {"simulation": "run"}
