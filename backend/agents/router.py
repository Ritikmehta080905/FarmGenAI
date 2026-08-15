"""
backend/agents/router.py

Conditional routing logic for the LangGraph StateGraph.
Determines edge transitions based on negotiation state and supply chain fallbacks.
"""

from backend.agents.state import NegotiationState

def route_after_planner(state: NegotiationState) -> str:
    """Route from planner to knowledge extraction."""
    return "knowledge_manager_agent"

def route_after_farmer(state: NegotiationState) -> str:
    """Determine the next step after the Farmer Agent makes a move."""
    status = state.get("status", "ACTIVE")
    
    if status in ("DEAL", "ACCEPT"):
        return "validator_agent"
        
    if status == "REJECT" or state.get("round", 0) >= state.get("max_rounds", 6):
        return "evaluate_escalation"
        
    return "buyer_agent"

def route_after_buyer(state: NegotiationState) -> str:
    """Determine the next step after the Buyer Agent makes a move."""
    status = state.get("status", "ACTIVE")
    
    if status in ("DEAL", "ACCEPT"):
        return "validator_agent"
        
    if status == "REJECT" or state.get("round", 0) >= state.get("max_rounds", 6):
        return "evaluate_escalation"
        
    return "farmer_agent"

def route_after_validator(state: NegotiationState) -> str:
    """Determine what happens after validation checks."""
    status = state.get("status", "ACTIVE")
    if status == "DEAL":
        return "transport_agent"
    # If invalid, it kicks back to negotiation or escalates if max rounds hit
    if state.get("round", 0) >= state.get("max_rounds", 6):
         return "evaluate_escalation"
    return "farmer_agent"

def evaluate_escalation(state: NegotiationState) -> str:
    """Supply chain fallback router. Triggers if direct sale fails."""
    spoilage = state.get("spoilage_days", 10)
    
    if spoilage > 7:
        return "warehouse_agent"
    elif spoilage >= 3:
        return "processor_agent"
    else:
        return "compost_agent"

def route_after_supply_chain(state: NegotiationState) -> str:
    """Route to reflection after supply chain nodes complete."""
    return "reflection_agent"

