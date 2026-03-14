from fastapi import APIRouter
from backend.controllers.negotiation_controller import (
    start_negotiation_controller,
    negotiation_status_controller
)
from backend.models.negotiation_model import (
    StartNegotiationRequest,
    NegotiationResponse,
    NegotiationStatusResponse
)

router = APIRouter(tags=["Negotiation"])


@router.post("/start-negotiation", response_model=NegotiationResponse)
def start(data: StartNegotiationRequest):
    return start_negotiation_controller(data.dict())


@router.get("/negotiation-status/{negotiation_id}", response_model=NegotiationStatusResponse)
def status(negotiation_id: str):
    return negotiation_status_controller(negotiation_id)