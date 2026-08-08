"""
backend/agents/state.py

Defines the core LangGraph state (NegotiationState) for the multi-agent negotiation engine.
Uses Annotated and operators to handle conversational memory (MessageGraph paradigm)
and append-only logs.
"""

import operator
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage


class NegotiationState(TypedDict):
    # Core Listing Information
    negotiation_id: str
    crop: str
    quantity: float
    min_price: float
    location: str
    spoilage_days: int
    
    # RAG / Knowledge Context (Fetched by KnowledgeManager)
    rag_context: str
    market_intelligence: str
    trust_context: str
    
    # Workflow & Strategy
    plan: str
    
    # Negotiation Loop State
    round: int
    max_rounds: int
    latest_farmer_ask: float
    latest_buyer_offer: float
    
    # Conversational Memory (LangGraph Reducer appends messages)
    history: Annotated[List[BaseMessage], operator.add]
    
    # Real-time WebSocket Logs (Reducer appends logs)
    logs: Annotated[List[str], operator.add]
    
    # End-State Decisions
    status: str  # ACTIVE | DEAL | REJECT | ESCALATED_STORAGE | ESCALATED_PROCESSING | ESCALATED_COMPOST
    selected_buyer: Optional[Dict[str, Any]]
    deal: Optional[Dict[str, Any]]
    supply_chain_booking: Optional[Dict[str, Any]]
    
    # Learning & Reflection
    reflection: Optional[str]
    recommendation: Optional[str]
