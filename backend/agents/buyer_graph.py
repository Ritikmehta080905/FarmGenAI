"""
backend/agents/buyer_graph.py
------------------------------------------------------------------------
LangGraph StateGraph workflow for Buyer Multi-Seller Negotiation Orchestration.

Workflow:
  input -> discover_candidates -> parallel_negotiations -> evaluate_outcomes -> select_winner -> format_chat_response -> END
"""

import logging
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END

from backend.services.buyer_orchestrator import buyer_orchestration_service

logger = logging.getLogger("BuyerGraph")


class BuyerOrchestrationGraphState(TypedDict):
    crop: str
    quantity: float
    target_price: float
    reservation_price: float
    budget: float
    location: str
    persona: str
    strategy: str
    sellers: Optional[List[Dict[str, Any]]]
    candidate_count: int
    candidates: List[Dict[str, Any]]
    negotiations: List[Dict[str, Any]]
    executable_deals: List[Dict[str, Any]]
    winner: Optional[Dict[str, Any]]
    status: str
    chat_transcript: str
    logs: List[str]


async def discover_candidates_node(state: BuyerOrchestrationGraphState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    logs.append(f"🔍 [Candidate Discovery] Finding top sellers for {state['quantity']}kg {state['crop']} in {state['location']}.")
    
    req_dict = {
        "crop": state["crop"],
        "quantity": state["quantity"],
        "target_price": state["target_price"],
        "max_price": state["reservation_price"],
        "reservation_price": state["reservation_price"],
        "budget": state["budget"],
        "location": state["location"],
        "persona": state.get("persona", "bulk_wholesaler"),
        "strategy": state.get("strategy", "balanced"),
        "sellers": state.get("sellers"),
    }
    candidates = await buyer_orchestration_service.get_top_candidates(req_dict, max_candidates=5)
    logs.append(f"📡 [Candidate Discovery] Found {len(candidates)} eligible sellers: {', '.join([c['name'] for c in candidates])}")
    
    return {
        "candidates": candidates,
        "candidate_count": len(candidates),
        "logs": logs,
    }


async def parallel_negotiations_node(state: BuyerOrchestrationGraphState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    candidates = state.get("candidates", [])
    logs.append(f"⚡ [Parallel Execution] Launching {len(candidates)} concurrent multi-round negotiation sessions.")

    req_dict = {
        "crop": state["crop"],
        "quantity": state["quantity"],
        "target_price": state["target_price"],
        "max_price": state["reservation_price"],
        "reservation_price": state["reservation_price"],
        "budget": state["budget"],
        "location": state["location"],
        "persona": state.get("persona", "bulk_wholesaler"),
        "strategy": state.get("strategy", "balanced"),
        "sellers": candidates,
    }

    orch_res = await buyer_orchestration_service.orchestrate_negotiation(req_dict, max_candidates=len(candidates))
    logs.append(f"📊 [Parallel Execution] Completed {len(orch_res.get('negotiations', []))} negotiations. Valid deals: {len(orch_res.get('executable_deals', []))}")

    return {
        "negotiations": orch_res.get("negotiations", []),
        "executable_deals": orch_res.get("executable_deals", []),
        "winner": orch_res.get("winner"),
        "status": orch_res.get("status", "NO_EXECUTABLE_DEAL"),
        "chat_transcript": orch_res.get("chat_transcript", ""),
        "logs": logs,
    }


async def format_chat_response_node(state: BuyerOrchestrationGraphState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    status = state.get("status")
    winner = state.get("winner")

    if winner and status == "DEAL_SELECTED":
        logs.append(f"🏆 [Final Selection] Deal locked with {winner['seller_name']} at ₹{winner['final_price']}/kg (Landed: ₹{winner['landed_cost_per_kg']}/kg).")
    else:
        logs.append("❌ [Final Selection] No executable deal found within reservation ceiling.")

    return {
        "logs": logs,
    }


# Build StateGraph
buyer_workflow = StateGraph(BuyerOrchestrationGraphState)
buyer_workflow.add_node("discover_candidates", discover_candidates_node)
buyer_workflow.add_node("parallel_negotiations", parallel_negotiations_node)
buyer_workflow.add_node("format_chat_response", format_chat_response_node)

buyer_workflow.set_entry_point("discover_candidates")
buyer_workflow.add_edge("discover_candidates", "parallel_negotiations")
buyer_workflow.add_edge("parallel_negotiations", "format_chat_response")
buyer_workflow.add_edge("format_chat_response", END)

buyer_graph_orchestrator = buyer_workflow.compile()
