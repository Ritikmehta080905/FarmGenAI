"""
backend/websocket/events.py

Strict, typed schemas for all WebSocket events traversing the frontend ↔ backend boundary.
Enforces the 20+ named event types rather than unstructured string logs.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class WSEventType(str, Enum):
    # System Lifecycle
    CONNECTION_ESTABLISHED = "CONNECTION_ESTABLISHED"
    NEGOTIATION_STARTED = "NEGOTIATION_STARTED"
    NEGOTIATION_COMPLETED = "NEGOTIATION_COMPLETED"
    NEGOTIATION_FAILED = "NEGOTIATION_FAILED"
    ERROR = "ERROR"

    # Agent Activity
    AGENT_THINKING = "AGENT_THINKING"
    AGENT_ACTION = "AGENT_ACTION"
    MARKET_DATA_FETCHED = "MARKET_DATA_FETCHED"
    RAG_CONTEXT_RETRIEVED = "RAG_CONTEXT_RETRIEVED"
    MATCHES_FOUND = "MATCHES_FOUND"

    # Negotiation Loop
    FARMER_OFFER_GENERATED = "FARMER_OFFER_GENERATED"
    BUYER_COUNTER_OFFER = "BUYER_COUNTER_OFFER"
    OFFER_VALIDATED = "OFFER_VALIDATED"
    OFFER_REJECTED = "OFFER_REJECTED"

    # Logistics & Supply Chain
    TRANSPORT_BID_RECEIVED = "TRANSPORT_BID_RECEIVED"
    WAREHOUSE_CAPACITY_CHECKED = "WAREHOUSE_CAPACITY_CHECKED"
    LOGISTICS_PLAN_FINALIZED = "LOGISTICS_PLAN_FINALIZED"

    # Fallback / Reflection
    STRATEGY_UPDATED = "STRATEGY_UPDATED"
    PROCESSOR_ESCALATION = "PROCESSOR_ESCALATION"
    COMPOST_ESCALATION = "COMPOST_ESCALATION"


class WSEventSchema(BaseModel):
    """
    Standard envelope for all WebSocket messages.
    """
    type: WSEventType = Field(..., description="The strict event type.")
    trace_id: str = Field(..., description="Unique trace ID tying this event to a specific E2E workflow run.")
    negotiation_id: Optional[str] = Field(None, description="The ID of the active negotiation, if applicable.")
    source_agent: str = Field(..., description="The component or agent that emitted this event (e.g., 'planner_node', 'farmer_agent').")
    timestamp: str = Field(..., description="ISO 8601 timestamp.")
    message: str = Field(..., description="Human-readable summary of the event.")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Structured data associated with the event.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context (e.g., crop, location, latency).")

    class Config:
        use_enum_values = True


def create_ws_event(
    event_type: WSEventType,
    trace_id: str,
    source_agent: str,
    message: str,
    negotiation_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Helper to create a serialized WS event dictionary."""
    import datetime
    return WSEventSchema(
        type=event_type,
        trace_id=trace_id,
        negotiation_id=negotiation_id,
        source_agent=source_agent,
        timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        message=message,
        payload=payload or {},
        metadata=metadata or {}
    ).model_dump()
