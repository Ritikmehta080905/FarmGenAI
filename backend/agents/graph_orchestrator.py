"""
backend/agents/graph_orchestrator.py

Stateful LangGraph orchestration engine for AgriNegotiator.
Implements Workflow Planner, Matching Engine, Farmer, Buyer, Validator, and Reflection nodes.
"""

import json
import re
import random
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END

from llm.llm_client import client as llm_client
from database.db import Database
from backend.agents.prompts import (
    PLANNER_PROMPT,
    MATCHING_ENGINE_PROMPT,
    FARMER_PROMPT,
    BUYER_PROMPT,
    VALIDATOR_PROMPT,
    REFLECTION_PROMPT,
)

# Define state structure
class NegotiationState(TypedDict):
    crop: str
    quantity: float
    min_price: float
    target_price: float
    spoilage_days: int
    location: str
    market_price: float
    round: int
    max_rounds: int
    history: List[Dict[str, Any]]
    buyer_profile: Optional[Dict[str, Any]]
    logs: List[str]
    status: str  # ACTIVE, DEAL, REJECT, ESCALATED_STORAGE, ESCALATED_PROCESSING, ESCALATED_COMPOST, FAILED
    proposed_scenario: str  # direct-sale, storage, processing, compost
    next_action: str
    deal: Optional[Dict[str, Any]]
    plan: Optional[str]
    reflection: Optional[str]
    selected_buyer: Optional[Dict[str, Any]]
    market_offers: List[Dict[str, Any]]
    user_id: Optional[str]
    latest_farmer_ask: Optional[float]
    latest_buyer_offer: Optional[float]
    buyers_list: List[Dict[str, Any]]


# --- 1. Workflow Planner Node ---
def planner_node(state: NegotiationState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    logs.append("📋 [Planner] Initiating negotiation workflow planner.")
    
    prompt = PLANNER_PROMPT.format(
        crop=state["crop"],
        quantity=state["quantity"],
        min_price=state["min_price"],
        location=state["location"],
        shelf_life=state["spoilage_days"],
        market_price=state["market_price"]
    )
    
    plan_text = llm_client.generate(prompt, max_tokens=150)
    if not plan_text:
        plan_text = f"Default plan: target bulk buyers in {state['location']} for {state['crop']}. Shelf-life={state['spoilage_days']} days."
        
    logs.append(f"📋 [Planner] Strategy plan generated: {plan_text.strip()}")
    return {
        "plan": plan_text.strip(),
        "logs": logs,
        "round": 0,
        "status": "ACTIVE"
    }


# --- 2. Matching Engine Node ---
def matching_engine_node(state: NegotiationState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    logs.append("📡 [Matching Engine] Querying suitable buyer profiles.")
    
    # Identify available buyers (either passed explicitly or from DB)
    state_buyers = state.get("buyers_list", [])
    if state_buyers:
        db_buyers = state_buyers
    else:
        db_buyers = Database.list_buyers()
        
    # Standardize to dict list
    raw_buyers = []
    for b in db_buyers:
        if isinstance(b, dict):
            raw_buyers.append(b)
        else:
            raw_buyers.append({
                "id": getattr(b, "id", f"buyer_{getattr(b, 'name', 'default').lower()}"),
                "name": getattr(b, "name", "Buyer"),
                "target_price": getattr(b, "target_price", state["min_price"]),
                "budget": getattr(b, "budget", 100000.0),
                "max_quantity": getattr(b, "max_quantity", state["quantity"]),
                "location": getattr(b, "location", "Market"),
                "strategy": getattr(b, "strategy", "default")
            })

    # Generate market offers list
    market_offers = []
    for profile in raw_buyers:
        if profile.get("kind") == "offer":
            continue
        offered_qty = min(state["quantity"], float(profile.get("max_quantity", state["quantity"])))
        budget_limited_price = float(profile.get("budget", 0)) / max(offered_qty, 1)
        
        strategy = profile.get("strategy", "").lower()
        if "restaurant" in strategy or "premium" in strategy:
            opening_bid = min(float(profile.get("target_price", state["min_price"])) * 0.85, budget_limited_price)
        else:
            opening_bid = min(float(profile.get("target_price", state["min_price"])) * 0.75, budget_limited_price, (state["market_price"] + 3) * 0.75)
            
        offer_price = round(max(1.0, opening_bid), 2)
        is_viable = offer_price >= state["min_price"]
        
        # Scoring logic
        distance_penalty = 0 if profile.get("location") == state["location"] else 0.2
        score = round((offer_price - distance_penalty) * 100 + (20.0 if profile.get("verified") else 0.0), 2)
        
        market_offers.append({
            "buyer_id": profile.get("id"),
            "buyer_name": profile.get("name"),
            "location": profile.get("location", "Market"),
            "strategy": profile.get("strategy", "Market Option"),
            "offered_price": offer_price,
            "offered_quantity": round(offered_qty, 2),
            "budget": float(profile.get("budget", 0)),
            "target_price": float(profile.get("target_price", state["min_price"])),
            "status": "VIABLE" if is_viable else "BELOW_MIN_PRICE",
            "score": score
        })
        
    market_offers.sort(key=lambda item: (item["status"] == "VIABLE", item["score"], item["offered_price"]), reverse=True)
    
    # Pick the best matched buyer
    selected_buyer = None
    if market_offers:
        best_offer = market_offers[0]
        selected_buyer = next((b for b in raw_buyers if b.get("id") == best_offer["buyer_id"] or b.get("name") == best_offer["buyer_name"]), None)
        
    if not selected_buyer and raw_buyers:
        selected_buyer = raw_buyers[0]
        
    if not selected_buyer:
        selected_buyer = {
            "id": "buyer_default",
            "name": "Marketplace Aggregator",
            "target_price": state["min_price"] * 1.1,
            "budget": state["min_price"] * state["quantity"] * 1.3,
            "max_quantity": state["quantity"],
            "location": state["location"],
            "strategy": "default"
        }
        
    logs.append(f"🎯 [Matching Engine] Matched with buyer: {selected_buyer['name']} (Target: ₹{selected_buyer.get('target_price')}/kg)")
    
    initial_buyer_offer = round(selected_buyer.get("target_price", state["min_price"]) * 0.75, 2)
    initial_farmer_ask = state["min_price"] + 10.0 # Ambitious start
    
    return {
        "buyer_profile": selected_buyer,
        "selected_buyer": selected_buyer,
        "latest_buyer_offer": initial_buyer_offer,
        "latest_farmer_ask": initial_farmer_ask,
        "market_offers": market_offers,
        "logs": logs
    }


# --- 3. Farmer Node ---
def farmer_node(state: NegotiationState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    history = list(state.get("history", []))
    current_round = state.get("round", 0) + 1
    
    buyer_offer = state.get("latest_buyer_offer")
    if buyer_offer is None:
        buyer_profile = state.get("buyer_profile") or {}
        buyer_offer = round(buyer_profile.get("target_price", state["min_price"]) * 0.75, 2)
        
    farmer_ask = state.get("latest_farmer_ask")
    if farmer_ask is None:
        farmer_ask = state["min_price"] + 10.0
        
    logs.append(f"👨‍🌾 [Farmer Node] Round {current_round}: Evaluating buyer offer of ₹{buyer_offer}/kg (Last Ask: ₹{farmer_ask}).")
    
    # 1. Accept check: if buyer offer meets farmer ask target within 2%
    if buyer_offer >= farmer_ask * 0.98:
        logs.append(f"👨‍🌾 [Farmer Node] Accepting offer ₹{buyer_offer}/kg (meets target expectations).")
        return {
            "status": "DEAL",
            "round": current_round,
            "latest_farmer_ask": buyer_offer,
            "logs": logs
        }
        
    # 2. Spoilage safety override
    spoilage = state["spoilage_days"]
    if spoilage <= 2:
        logs.append("⚠️ [Farmer Node] Spoilage window critical (<= 2 days). Accepting near-min bid or escalating.")
        if buyer_offer >= state["min_price"] * 0.85:
            return {
                "status": "DEAL",
                "round": current_round,
                "latest_farmer_ask": buyer_offer,
                "logs": logs
            }
        else:
            return {
                "status": "REJECT",
                "round": current_round,
                "logs": logs
            }
            
    # Concession calculation (Farmer moves down 20% toward buyer's offer)
    gap = farmer_ask - buyer_offer
    concession = (gap * 0.2) + random.uniform(0.1, 0.4)
    counter_price = round(buyer_offer + concession, 2)
    counter_price = max(state["min_price"], counter_price)
    
    # Make sure we don't counter higher than our previous ask
    if counter_price >= farmer_ask:
        counter_price = round(farmer_ask - 0.5, 2)
    counter_price = max(state["min_price"], counter_price)
    
    # If the counter is close enough to buyer offer (within 3%), we can just accept it
    if buyer_offer >= counter_price * 0.98:
        logs.append(f"👨‍🌾 [Farmer Node] Accept offer ₹{buyer_offer}/kg close to counter ask ₹{counter_price}/kg.")
        return {
            "status": "DEAL",
            "round": current_round,
            "latest_farmer_ask": buyer_offer,
            "logs": logs
        }
        
    logs.append(f"👨‍🌾 [Farmer Node] Proposing counter ask: ₹{counter_price}/kg.")
    new_offer_log = {
        "round": current_round,
        "agent": "Farmer",
        "price": counter_price,
        "decision": "COUNTER",
        "quantity": state["quantity"],
        "message": "I am looking for a price closer to my target, though I am willing to meet part-way."
    }
    history.append(new_offer_log)
    
    return {
        "round": current_round,
        "history": history,
        "latest_farmer_ask": counter_price,
        "latest_buyer_offer": buyer_offer,
        "logs": logs
    }


# --- 4. Buyer Node ---
def buyer_node(state: NegotiationState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    history = list(state.get("history", []))
    current_round = state.get("round", 0)
    
    farmer_ask = state.get("latest_farmer_ask", state["min_price"] + 10.0)
    buyer_profile = state["buyer_profile"]
    
    buyer_offer = state.get("latest_buyer_offer")
    if buyer_offer is None:
        buyer_offer = round(buyer_profile.get("target_price", state["min_price"]) * 0.75, 2)
        
    logs.append(f"🤝 [Buyer Node] Round {current_round}: Evaluating farmer ask of ₹{farmer_ask}/kg (Last Bid: ₹{buyer_offer}).")
    
    # 1. Accept check: if farmer's ask is below buyer's procurement target or within 3%
    target_threshold = buyer_profile.get("target_price", state["min_price"]) * 1.03
    if farmer_ask <= target_threshold:
        logs.append(f"🤝 [Buyer Node] Accepting farmer ask at ₹{farmer_ask} (within procurement margin).")
        return {
            "status": "DEAL",
            "latest_buyer_offer": farmer_ask,
            "logs": logs
        }
        
    # Concession calculation (Buyer moves up 20% toward farmer's ask)
    gap = farmer_ask - buyer_offer
    concession = (gap * 0.2) + random.uniform(0.1, 0.4)
    counter_price = round(buyer_offer + concession, 2)
    counter_price = min(farmer_ask, counter_price)
    
    # Make sure we don't counter lower than our previous offer
    if counter_price <= buyer_offer:
        counter_price = round(buyer_offer + 0.5, 2)
    counter_price = min(farmer_ask, counter_price)
    
    # budget checks
    max_viable = float(buyer_profile.get("budget", 100000)) / state["quantity"]
    counter_price = min(max_viable, counter_price)
    
    # If counter price is extremely close to farmer ask, we just accept
    if farmer_ask <= counter_price * 1.03:
        logs.append(f"🤝 [Buyer Node] Accept farmer ask at ₹{farmer_ask} (close to counter ₹{counter_price}/kg).")
        return {
            "status": "DEAL",
            "latest_buyer_offer": farmer_ask,
            "logs": logs
        }
        
    logs.append(f"🤝 [Buyer Node] Proposing counter bid: ₹{counter_price}/kg.")
    new_offer_log = {
        "round": current_round,
        "agent": "Buyer",
        "price": counter_price,
        "decision": "COUNTER",
        "quantity": state["quantity"],
        "message": "I'm offering a slight increase to reach a compromise."
    }
    history.append(new_offer_log)
    
    return {
        "history": history,
        "latest_buyer_offer": counter_price,
        "logs": logs
    }


# --- 5. Validator Node ---
def validator_node(state: NegotiationState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    logs.append("⚖️ [Validator Node] Validating deal constraints and terms.")
    
    deal_price = state.get("latest_buyer_offer", 0)
    
    budget = state["buyer_profile"].get("budget", 100000)
    total_cost = deal_price * state["quantity"]
    
    valid = True
    reason = "Deal terms fully validated."
    
    if total_cost > budget:
        valid = False
        reason = f"Budget exceeded: Deal cost ₹{total_cost:.2f} > Buyer budget ₹{budget:.2f}"
    elif deal_price < state["min_price"] and state["spoilage_days"] > 2:
        valid = False
        reason = f"Price under min threshold: ₹{deal_price} < minimum ₹{state['min_price']}"
        
    logs.append(f"⚖️ [Validator Node] Outcome: Valid={valid}. {reason}")
    
    if valid:
        deal = {
            "buyer_name": state["buyer_profile"]["name"],
            "price": deal_price,
            "quantity": state["quantity"],
            "status": "DEAL",
            "buyer_id": state["buyer_profile"]["id"]
        }
        return {
            "status": "DEAL",
            "deal": deal,
            "logs": logs
        }
    else:
        return {
            "status": "REJECT",
            "logs": logs
        }


# --- 6. Reflection Node ---
def reflection_node(state: NegotiationState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    logs.append("🧐 [Reflection Node] Executing post-negotiation analysis.")
    
    history_str = "\n".join([f"Round {h.get('round')}: {h.get('agent')} bid/ask ₹{h.get('price')}" for h in state.get("history", [])])
    
    prompt = REFLECTION_PROMPT.format(
        crop=state["crop"],
        status=state["status"],
        rounds=state["round"],
        history=history_str,
        summary=f"Final state: {state['status']}"
    )
    
    reflection_text = llm_client.generate(prompt, max_tokens=150)
    if not reflection_text:
        reflection_text = "Analysis: Negotiation finalized. Checked metrics. Falls back within parameters."
        
    logs.append(f"🧐 [Reflection Node] Insights: {reflection_text.strip()}")
    
    # --- Supply Chain Fallback (Escalation Path if no deal was reached) ---
    final_status = state["status"]
    deal = state.get("deal")
    
    if final_status != "DEAL":
        logs.append("⚠️ [Reflection Node] Direct sale failed. Initiating supply chain fallbacks.")
        
        # 1. Warehouse storage fallback
        spoilage = state["spoilage_days"]
        storage_cost = 1.8 * state["quantity"] * spoilage
        
        if spoilage > 2 and storage_cost < state["market_price"] * state["quantity"] * 0.3:
            logs.append(f"🏗️ [Reflection Node] Storage fallback chosen. Storing at WarehouseAgent.")
            final_status = "ESCALATED_STORAGE"
            deal = {
                "type": "STORAGE",
                "price": round(state["market_price"] * 0.9, 2),
                "quantity": state["quantity"],
                "warehouse": "WarehouseAgent",
                "storage_cost": storage_cost
            }
        # 2. Processor fallback
        elif state["market_price"] * 0.8 >= state["min_price"] * 0.6:
            logs.append(f"⚙️ [Reflection Node] Processor fallback chosen. Selling to ProcessorAgent.")
            final_status = "ESCALATED_PROCESSING"
            deal = {
                "type": "PROCESSING",
                "price": round(state["market_price"] * 0.8, 2),
                "quantity": state["quantity"],
                "processor": "ProcessorAgent"
            }
        # 3. Compost fallback
        else:
            logs.append("♻️ [Reflection Node] Zero-waste fallback: sending to CompostAgent.")
            final_status = "ESCALATED_COMPOST"
            deal = {
                "type": "COMPOST",
                "price": 8.0,
                "quantity": state["quantity"],
                "compost": "CompostAgent"
            }
            
    return {
        "status": final_status,
        "deal": deal,
        "reflection": reflection_text.strip(),
        "logs": logs
    }


# --- Conditional Routing Rules ---

def route_after_farmer(state: NegotiationState):
    if state["status"] in ("DEAL", "ACCEPT"):
        return "validator_agent"
    elif state["status"] == "REJECT" or state["round"] >= state["max_rounds"]:
        return "reflection_agent"
    else:
        return "buyer_agent"

def route_after_buyer(state: NegotiationState):
    if state["status"] in ("DEAL", "ACCEPT"):
        return "validator_agent"
    elif state["status"] == "REJECT" or state["round"] >= state["max_rounds"]:
        return "reflection_agent"
    else:
        return "farmer_agent"

def route_after_validator(state: NegotiationState):
    return "reflection_agent"


# --- Compile Graph ---

workflow = StateGraph(NegotiationState)

workflow.add_node("planner_agent", planner_node)
workflow.add_node("matching_agent", matching_engine_node)
workflow.add_node("farmer_agent", farmer_node)
workflow.add_node("buyer_agent", buyer_node)
workflow.add_node("validator_agent", validator_node)
workflow.add_node("reflection_agent", reflection_node)

workflow.set_entry_point("planner_agent")

workflow.add_edge("planner_agent", "matching_agent")
workflow.add_edge("matching_agent", "farmer_agent")

workflow.add_conditional_edges(
    "farmer_agent",
    route_after_farmer,
    {
        "validator_agent": "validator_agent",
        "reflection_agent": "reflection_agent",
        "buyer_agent": "buyer_agent"
    }
)

workflow.add_conditional_edges(
    "buyer_agent",
    route_after_buyer,
    {
        "validator_agent": "validator_agent",
        "reflection_agent": "reflection_agent",
        "farmer_agent": "farmer_agent"
    }
)

workflow.add_conditional_edges(
    "validator_agent",
    route_after_validator,
    {
        "reflection_agent": "reflection_agent"
    }
)

workflow.add_edge("reflection_agent", END)

graph_orchestrator = workflow.compile()
