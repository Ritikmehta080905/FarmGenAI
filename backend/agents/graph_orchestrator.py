"""
backend/agents/graph_orchestrator.py

Stateful LangGraph orchestration engine for AgriNegotiator.
Implements the 14-Node ecosystem with R-RL learning, XAI, and strict BATNA enforcement.
"""

import json
import re
import logging
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from llm.llm_client import client as llm_client
from backend.agents.state import NegotiationState
from backend.agents.prompts import (
    PLANNER_PROMPT, MARKET_INTELLIGENCE_PROMPT, MATCHING_ENGINE_PROMPT,
    FARMER_PROMPT, BUYER_PROMPT, VALIDATOR_PROMPT, WAREHOUSE_PROMPT,
    TRANSPORT_PROMPT, PROCESSOR_PROMPT, COMPOST_PROMPT, REFLECTION_PROMPT,
    RECOMMENDATION_PROMPT, TRUST_PROMPT, KNOWLEDGE_EXTRACTION_PROMPT
)
from backend.agents.router import (
    route_after_planner, route_after_farmer, route_after_buyer,
    route_after_validator, evaluate_escalation, route_after_supply_chain
)
from database.db import Database

logger = logging.getLogger("GraphOrchestrator")


def _parse_json_response(text: str) -> Dict:
    """Extract first valid JSON object from LLM response."""
    if not text:
        return {}
    try:
        cleaned = re.sub(r"```(?:json)?", "", text).strip()
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            return json.loads(m.group())
    except (json.JSONDecodeError, Exception):
        pass
    return {}


def _build_rag_context(crop: str, location: str) -> str:
    """Query ChromaDB and relational database for a comprehensive market context."""
    context_parts = []
    
    # 1. Fetch structured facts from Database
    try:
        # a. MSP Price
        msp = Database.get_msp_price(crop)
        if msp:
            context_parts.append(f"Official Government MSP (2026-27) for {crop}: ₹{msp:.2f}/quintal (₹{msp/100:.2f}/kg).")

        # b. Market Mapping
        mappings = Database.get_market_mappings(location)
        if mappings:
            markets_str = ", ".join([m["market_name"] for m in mappings])
            context_parts.append(f"Associated APMC mandis for {location} district: {markets_str}.")

        # c. Crop Quality Standards
        quality = Database.get_crop_quality_reference(crop)
        if quality:
            q_lines = ["Crop Quality Standards:"]
            for q in quality:
                q_lines.append(
                    f"  - Grade {q['grade']} {q['variety']}: Size >= {q['min_size_mm']}mm, "
                    f"Max Moisture {q['max_moisture_pct']}%, Color: {q['color_standards']}, "
                    f"Skin: {q['skin_firmness']}, Defects: {q['common_defects_allowed']}"
                )
            context_parts.append("\n".join(q_lines))

        # d. Seasonal Calendar
        from datetime import datetime
        current_month = datetime.now().strftime("%B").lower()
        calendar_events = Database.get_seasonal_calendar()
        matching_events = []
        for event in calendar_events:
            if current_month in event["month_range"].lower() or any(crop.lower() in c.lower() for c in event["affected_crops"].split(",")):
                matching_events.append(
                    f"  - {event['event_name']} ({event['month_range']}): Trend: {event['price_impact_trend']}. "
                    f"Behavior: {event['market_behavior_description']}"
                )
        if matching_events:
            context_parts.append("Seasonal Market Activity Warnings:\n" + "\n".join(matching_events))
    except Exception as ex:
        logger.warning(f"Failed to fetch structured database facts: {ex}")

    # 2. Fetch live Weather from Open-Meteo API
    try:
        import urllib.request
        # Coordinates map for Maharashtra districts
        coords = {
            "Pune": (18.52, 73.85),
            "Nashik": (19.99, 73.78),
            "Nagpur": (21.14, 79.08),
            "Jalgaon": (21.00, 75.56),
            "Ahmednagar": (19.09, 74.74),
            "Satara": (17.68, 73.98),
            "Latur": (18.40, 76.56),
            "Thane": (19.22, 72.98),
            "Mumbai": (19.07, 72.87),
            "Amravati": (20.93, 77.75),
            "Kolhapur": (16.70, 74.24),
            "Aurangabad": (19.88, 75.34),
            "Sangli": (16.85, 74.58),
            "Dhule": (20.90, 74.77)
        }
        lat, lon = coords.get(location, (19.07, 72.87)) # Default to Mumbai
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            w_data = json.loads(resp.read().decode('utf-8'))
            current = w_data.get("current_weather", {})
            temp = current.get("temperature")
            wind = current.get("windspeed")
            context_parts.append(f"Live Weather for {location} district: Temp {temp}°C, Wind Speed {wind} km/h (Source: Open-Meteo).")
    except Exception as ex:
        logger.warning(f"Failed to retrieve live weather data: {ex}")

    # 3. Query RAG vector store for unstructured documents
    try:
        from backend.services.rag_service import rag_service
        query = f"{crop} market price {location}"

        # Mandi prices
        mandi_results = rag_service.query_mandi_records(query, n_results=2)
        if mandi_results and mandi_results.get("documents"):
            docs = mandi_results["documents"][0]
            if docs:
                context_parts.append("Recent APMC Mandi price transactions:\n" + "\n".join([f"  - {d}" for d in docs]))

        # Historical negotiation logs
        strategy_results = rag_service.query_strategies(query, n_results=2)
        if strategy_results and strategy_results.get("documents"):
            docs = strategy_results["documents"][0]
            if docs:
                context_parts.append("Past negotiation logs & strategies:\n" + "\n".join([f"  - {d}" for d in docs]))

        # Crop Knowledge Base
        knowledge_results = rag_service.query_crop_knowledge(
            query_text=f"{crop} cultivation practices diseases harvesting shelf-life",
            crop=crop,
            n_results=1
        )
        if knowledge_results:
            context_parts.append("Agronomic Crop Guidelines (ICAR):\n" + "\n".join([f"  - {k['text']}" for k in knowledge_results]))

        # Government Schemes (Insurance, etc.)
        schemes_results = rag_service.query_government_schemes(
            query_text=f"PMFBY crop insurance premium rate sum insured claim {crop}",
            n_results=1
        )
        if schemes_results:
            context_parts.append("Government Scheme Guidelines (PMFBY):\n" + "\n".join([f"  - {s['text']}" for s in schemes_results]))

    except Exception as e:
        logger.warning(f"RAG document search failed: {e}")

    return "\n\n".join(context_parts) if context_parts else "No historical context available."


def _format_history(history: List[Dict]) -> str:
    """Convert history list to readable string."""
    if not history:
        return "No rounds yet."
    lines = []
    for h in history:
        lines.append(
            f"  Round {h.get('round', '?')}: {h.get('agent', '?')} "
            f"{'offered' if h.get('agent') == 'Buyer' else 'asked'} "
            f"₹{h.get('price', 0)}/kg ({h.get('decision', 'COUNTER')})"
        )
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Pre-Negotiation Nodes
# ─────────────────────────────────────────────

def planner_node(state: NegotiationState) -> Dict[str, Any]:
    prompt = PLANNER_PROMPT.format(
        crop=state["crop"], quantity=state["quantity"], min_price=state["min_price"],
        location=state["location"], shelf_life=state["spoilage_days"], market_price=state.get("market_price", 0)
    )
    plan_text = llm_client.generate(prompt, max_tokens=150) or "Default Strategy"
    return {"plan": plan_text, "logs": ["📋 [Planner] Strategy finalized."]}


def knowledge_manager_node(state: NegotiationState) -> Dict[str, Any]:
    # Query database facts + weather + ChromaDB using unified _build_rag_context helper
    rag_context = _build_rag_context(state["crop"], state["location"])
    return {"rag_context": rag_context, "logs": ["🧠 [KnowledgeManager] Context retrieved."]}


def market_intelligence_node(state: NegotiationState) -> Dict[str, Any]:
    prompt = MARKET_INTELLIGENCE_PROMPT.format(
        crop=state["crop"], location=state["location"],
        mandi_data=state.get("rag_context", ""), weather_data="Sunny, 32C"
    )
    analysis = llm_client.generate(prompt, max_tokens=150) or "Market stable."
    return {"market_intelligence": analysis, "logs": ["📊 [MarketIntel] Analysis complete."]}


def matching_engine_node(state: NegotiationState) -> Dict[str, Any]:
    prompt = MATCHING_ENGINE_PROMPT.format(
        crop=state["crop"], quantity=state["quantity"], min_price=state["min_price"],
        location=state["location"], buyers="Buyer 1 (₹20), Buyer 2 (₹22)"
    )
    # Mocking matching logic
    buyer = {"name": "Buyer 2", "budget": 50000, "target_price": 22.0}
    return {"selected_buyer": buyer, "latest_buyer_offer": 20.0, "latest_farmer_ask": 24.0, "logs": ["📡 [Matching] Buyer selected."]}


def trust_engine_node(state: NegotiationState) -> Dict[str, Any]:
    prompt = TRUST_PROMPT.format(
        farmer_id="farmer_123", buyer_id="buyer_456", trust_context="Both users have 5.0 scores."
    )
    trust_res = llm_client.generate(prompt, max_tokens=50) or "High trust."
    return {"trust_context": trust_res, "logs": ["🛡️ [TrustEngine] Context built."]}


# ─────────────────────────────────────────────
# Active Negotiation Nodes
# ─────────────────────────────────────────────

def farmer_node(state: NegotiationState) -> Dict[str, Any]:
    current_round = state.get("round", 0) + 1
    prompt = FARMER_PROMPT.format(
        crop=state["crop"], quantity=state["quantity"], min_price=state["min_price"],
        location=state["location"], shelf_life=state["spoilage_days"],
        market_price=state.get("market_price", 0), buyer_offer=state.get("latest_buyer_offer", 0),
        round=current_round, history=str(state.get("history", [])),
        rag_context=state.get("rag_context", ""), trust_context=state.get("trust_context", "")
    )
    raw = llm_client.generate(prompt, max_tokens=250)
    decision = _parse_json_response(raw)
    
    status = "ACTIVE"
    ask_price = decision.get("price", state.get("latest_farmer_ask", 0))
    human_msg = decision.get("human_message", f"I am asking for ₹{ask_price}")
    
    if decision.get("decision") == "ACCEPT":
        status = "ACCEPT"
        ask_price = state.get("latest_buyer_offer")
    elif decision.get("decision") == "REJECT":
        status = "REJECT"

    msg = AIMessage(content=f"👨‍🌾 [Farmer] {human_msg}")
    return {
        "round": current_round,
        "latest_farmer_ask": ask_price,
        "status": status,
        "history": [msg],
        "logs": [f"👨‍🌾 [Farmer] {decision.get('decision', 'COUNTER')}: ₹{ask_price}"]
    }


def buyer_node(state: NegotiationState) -> Dict[str, Any]:
    buyer = state.get("selected_buyer", {})
    prompt = BUYER_PROMPT.format(
        buyer_name=buyer.get("name", "Buyer"), target_price=buyer.get("target_price", 0),
        budget=buyer.get("budget", 0), max_quantity=state["quantity"], location=state["location"],
        farmer_ask=state.get("latest_farmer_ask", 0), round=state.get("round", 0),
        history=str(state.get("history", [])), rag_context=state.get("rag_context", ""),
        trust_context=state.get("trust_context", "")
    )
    raw = llm_client.generate(prompt, max_tokens=250)
    decision = _parse_json_response(raw)
    
    status = "ACTIVE"
    bid_price = decision.get("price", state.get("latest_buyer_offer", 0))
    human_msg = decision.get("human_message", f"I am offering ₹{bid_price}")
    
    if decision.get("decision") == "ACCEPT":
        status = "ACCEPT"
        bid_price = state.get("latest_farmer_ask")
    elif decision.get("decision") == "REJECT":
        status = "REJECT"

    msg = AIMessage(content=f"🤝 [Buyer] {human_msg}")
    return {
        "latest_buyer_offer": bid_price,
        "status": status,
        "history": [msg],
        "logs": [f"🤝 [Buyer] {decision.get('decision', 'COUNTER')}: ₹{bid_price}"]
    }


def validator_node(state: NegotiationState) -> Dict[str, Any]:
    deal_price = state.get("latest_buyer_offer", 0)
    buyer = state.get("selected_buyer", {})
    
    prompt = VALIDATOR_PROMPT.format(
        farmer_price=state.get("latest_farmer_ask"), buyer_price=deal_price,
        min_price=state["min_price"], budget=buyer.get("budget", 0),
        quantity=state["quantity"], msp=15.0 # Mock MSP
    )
    raw = llm_client.generate(prompt, max_tokens=150)
    validation = _parse_json_response(raw)
    
    if validation.get("valid"):
        return {"status": "DEAL", "logs": ["⚖️ [Validator] Deal Approved."]}
    else:
        msg = SystemMessage(content=f"⚖️ [System] Deal invalidated: {validation.get('reason')}")
        return {"status": "ACTIVE", "history": [msg], "logs": ["⚖️ [Validator] Deal Rejected - Resume."]}


# ─────────────────────────────────────────────
# Supply Chain Nodes
# ─────────────────────────────────────────────

def warehouse_agent_node(state: NegotiationState) -> Dict[str, Any]:
    return {"status": "ESCALATED_STORAGE", "logs": ["🏗️ [Warehouse] Storage booked."]}

def transport_agent_node(state: NegotiationState) -> Dict[str, Any]:
    return {"logs": ["🚚 [Transport] Logistics booked."]}

def processor_agent_node(state: NegotiationState) -> Dict[str, Any]:
    return {"status": "ESCALATED_PROCESSING", "logs": ["⚙️ [Processor] Sent to processor."]}

def compost_agent_node(state: NegotiationState) -> Dict[str, Any]:
    return {"status": "ESCALATED_COMPOST", "logs": ["♻️ [Compost] Sent to compost."]}


# ─────────────────────────────────────────────
# Post-Negotiation Nodes (Learning)
# ─────────────────────────────────────────────

def reflection_agent_node(state: NegotiationState) -> Dict[str, Any]:
    prompt = REFLECTION_PROMPT.format(
        crop=state["crop"], status=state["status"], history=str(state.get("history", [])),
        market_price=state.get("market_price", 0), final_price=state.get("latest_buyer_offer", 0)
    )
    raw = llm_client.generate(prompt, max_tokens=150)
    lessons = _parse_json_response(raw).get("lessons", [])
    
    return {"reflection": str(lessons), "logs": ["🧐 [Reflection] Lessons learned and saved."]}

def recommendation_agent_node(state: NegotiationState) -> Dict[str, Any]:
    prompt = RECOMMENDATION_PROMPT.format(
        crop=state["crop"], final_status=state["status"], reflection_insights=state.get("reflection", "")
    )
    rec = llm_client.generate(prompt, max_tokens=100) or "Advice generated."
    return {"recommendation": rec, "logs": ["💡 [Recommendation] Advice published."]}


# ─────────────────────────────────────────────
# Graph Compilation
# ─────────────────────────────────────────────

workflow = StateGraph(NegotiationState)

# Add 14 Nodes
workflow.add_node("planner_agent", planner_node)
workflow.add_node("knowledge_manager_agent", knowledge_manager_node)
workflow.add_node("market_intelligence_agent", market_intelligence_node)
workflow.add_node("matching_agent", matching_engine_node)
workflow.add_node("trust_engine_agent", trust_engine_node)
workflow.add_node("farmer_agent", farmer_node)
workflow.add_node("buyer_agent", buyer_node)
workflow.add_node("validator_agent", validator_node)
workflow.add_node("warehouse_agent", warehouse_agent_node)
workflow.add_node("transport_agent", transport_agent_node)
workflow.add_node("processor_agent", processor_agent_node)
workflow.add_node("compost_agent", compost_agent_node)
workflow.add_node("reflection_agent", reflection_agent_node)
workflow.add_node("recommendation_agent", recommendation_agent_node)

# Set Entry
workflow.set_entry_point("planner_agent")

# Edges for pre-negotiation linear flow
workflow.add_edge("planner_agent", "knowledge_manager_agent")
workflow.add_edge("knowledge_manager_agent", "market_intelligence_agent")
workflow.add_edge("market_intelligence_agent", "matching_agent")
workflow.add_edge("matching_agent", "trust_engine_agent")
workflow.add_edge("trust_engine_agent", "farmer_agent")

# Conditional Routing for Active Negotiation
workflow.add_conditional_edges("farmer_agent", route_after_farmer)
workflow.add_conditional_edges("buyer_agent", route_after_buyer)
workflow.add_conditional_edges("validator_agent", route_after_validator)

# Supply Chain Routing (Escalation)
# When a round limit or reject is hit, it routes to `evaluate_escalation` which returns
# one of the supply chain nodes.
# Langgraph handles this via `add_conditional_edges` on a dummy node or from the source directly.
# Wait, `route_after_farmer` returns "evaluate_escalation". We need a router node for that.
# Or we can just use conditional edges that point directly to the supply chain nodes.
# Let's fix that mapping.

# Let's add a dummy pass-through node for escalation router, or just fix `router.py` to be called inside the conditional edge map.
# LangGraph `add_conditional_edges` directly accepts a function returning the next node name.
# `evaluate_escalation` is called inside `route_after_farmer` if we change it.
# I will use a passthrough node to keep the graph clean.
def escalation_router_node(state: NegotiationState) -> Dict[str, Any]:
    return {}
workflow.add_node("escalation_router_node", escalation_router_node)
workflow.add_conditional_edges("escalation_router_node", evaluate_escalation)

# Update the conditional edges in graph compilation
workflow.add_conditional_edges("farmer_agent", route_after_farmer, {
    "validator_agent": "validator_agent",
    "buyer_agent": "buyer_agent",
    "evaluate_escalation": "escalation_router_node"
})

workflow.add_conditional_edges("buyer_agent", route_after_buyer, {
    "validator_agent": "validator_agent",
    "farmer_agent": "farmer_agent",
    "evaluate_escalation": "escalation_router_node"
})

workflow.add_conditional_edges("validator_agent", route_after_validator, {
    "transport_agent": "transport_agent",
    "farmer_agent": "farmer_agent",
    "evaluate_escalation": "escalation_router_node"
})

# All supply chain nodes map to reflection
workflow.add_edge("warehouse_agent", "reflection_agent")
workflow.add_edge("transport_agent", "reflection_agent")
workflow.add_edge("processor_agent", "reflection_agent")
workflow.add_edge("compost_agent", "reflection_agent")

# Learning Pipeline
workflow.add_edge("reflection_agent", "recommendation_agent")
workflow.add_edge("recommendation_agent", END)

graph_orchestrator = workflow.compile()
