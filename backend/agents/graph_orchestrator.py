"""
backend/agents/graph_orchestrator.py

Stateful LangGraph orchestration engine for AgriNegotiator.
Implements Workflow Planner, Matching Engine, Farmer, Buyer,
Validator, Reflection, Market Intelligence, and Recommendation nodes.
Uses structured LangChain PromptTemplates with JSON output parsing.
RAG context is injected into Farmer and Buyer agent prompts.
"""

import json
import re
import random
import logging
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
    MARKET_INTELLIGENCE_PROMPT,
    RECOMMENDATION_PROMPT,
)

logger = logging.getLogger("GraphOrchestrator")


# ─────────────────────────────────────────────
# Shared LangGraph State
# ─────────────────────────────────────────────

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
    status: str            # ACTIVE | DEAL | REJECT | ESCALATED_STORAGE | ESCALATED_PROCESSING | ESCALATED_COMPOST
    proposed_scenario: str
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
    rag_context: Optional[str]               # Injected market + strategy context
    market_intelligence: Optional[str]       # Market analysis output
    recommendation: Optional[str]           # Recommendation agent output


# ─────────────────────────────────────────────
# Helper: safe JSON parse from LLM output
# ─────────────────────────────────────────────

async def _parse_json_response(text: str) -> Optional[Dict]:
    """Extract first valid JSON object from LLM response."""
    if not text:
        return None
    try:
        # Strip markdown fences if present
        cleaned = re.sub(r"```(?:json)?", "", text).strip()
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            return json.loads(m.group())
    except (json.JSONDecodeError, Exception):
        pass
    return None


async def _build_rag_context(crop: str, location: str) -> str:
    """Query ChromaDB for market prices and strategy context."""
    try:
        from backend.services.rag_service import rag_service
        query = f"{crop} market price {location}"

        mandi_results = await rag_service.query_mandi_records(query, n_results=2)
        strategy_results = await rag_service.query_strategies(query, n_results=2)

        context_parts = []

        if mandi_results and mandi_results.get("documents"):
            docs = mandi_results["documents"][0]
            if docs:
                context_parts.append("Recent mandi prices:\n" + "\n".join(docs[:2]))

        if strategy_results and strategy_results.get("documents"):
            docs = strategy_results["documents"][0]
            if docs:
                context_parts.append("Past negotiation strategies:\n" + "\n".join(docs[:2]))

        return "\n\n".join(context_parts) if context_parts else "No historical context available."
    except Exception as e:
        logger.warning(f"RAG context fetch failed: {e}")
        return "No historical context available."


async def _format_history(history: List[Dict]) -> str:
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
# Node 1: Workflow Planner
# ─────────────────────────────────────────────

async def planner_node(state: NegotiationState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    logs.append("📋 [Planner] Initiating negotiation workflow planner.")

    # Fetch RAG context early — shared across all downstream agents
    rag_context = await _build_rag_context(state["crop"], state["location"])

    prompt = PLANNER_PROMPT.format(
        crop=state["crop"],
        quantity=state["quantity"],
        min_price=state["min_price"],
        location=state["location"],
        shelf_life=state["spoilage_days"],
        market_price=state["market_price"]
    )

    plan_text = llm_client.generate(prompt, max_tokens=200)
    if not plan_text:
        plan_text = (
            f"Strategy: Target bulk and premium buyers in {state['location']} "
            f"for {state['crop']}. Shelf-life={state['spoilage_days']} days. "
            f"Spoilage risk={'HIGH' if state['spoilage_days'] <= 3 else 'MEDIUM' if state['spoilage_days'] <= 7 else 'LOW'}. "
            f"Opening target ₹{round(state['min_price'] * 1.2, 2)}/kg."
        )

    logs.append(f"📋 [Planner] Strategy: {plan_text.strip()[:120]}...")
    return {
        "plan": plan_text.strip(),
        "logs": logs,
        "round": 0,
        "status": "ACTIVE",
        "rag_context": rag_context,
    }


# ─────────────────────────────────────────────
# Node 2: Market Intelligence
# ─────────────────────────────────────────────

async def market_intelligence_node(state: NegotiationState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    logs.append("📊 [Market Intelligence] Analyzing market conditions.")

    prompt = MARKET_INTELLIGENCE_PROMPT.format(
        crop=state["crop"],
        location=state["location"],
        season="Kharif" if state["spoilage_days"] <= 90 else "Rabi",
        mandi_data=state.get("rag_context", "No mandi data available."),
        weather_data=f"Location: {state['location']}. Data pending."
    )

    analysis = llm_client.generate(prompt, max_tokens=200)
    if not analysis:
        # Fallback deterministic analysis
        if state["market_price"] > state["min_price"] * 1.1:
            analysis = f"Market is bullish for {state['crop']}. Recommended band: ₹{round(state['market_price'] * 0.9, 2)} - ₹{round(state['market_price'] * 1.15, 2)}/kg."
        else:
            analysis = f"Market is at par for {state['crop']}. Recommended band: ₹{state['min_price']} - ₹{round(state['market_price'] * 1.05, 2)}/kg."

    logs.append(f"📊 [Market Intelligence] {analysis[:100]}...")
    return {
        "market_intelligence": analysis,
        "logs": logs,
    }


# ─────────────────────────────────────────────
# Node 3: Matching Engine
# ─────────────────────────────────────────────

async def matching_engine_node(state: NegotiationState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    logs.append("📡 [Matching Engine] Querying suitable buyer profiles.")

    state_buyers = state.get("buyers_list", [])
    db_buyers = state_buyers if state_buyers else await Database.list_buyers_async()

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
            opening_bid = min(
                float(profile.get("target_price", state["min_price"])) * 0.75,
                budget_limited_price,
                (state["market_price"] + 3) * 0.75
            )

        offer_price = round(max(1.0, opening_bid), 2)
        is_viable = offer_price >= state["min_price"]

        distance_penalty = 0 if profile.get("location") == state["location"] else 0.2
        score = round(
            (offer_price - distance_penalty) * 100
            + (20.0 if profile.get("verified") else 0.0),
            2
        )

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

    market_offers.sort(
        key=lambda item: (item["status"] == "VIABLE", item["score"], item["offered_price"]),
        reverse=True
    )

    selected_buyer = None
    if market_offers:
        best = market_offers[0]
        selected_buyer = next(
            (b for b in raw_buyers if b.get("id") == best["buyer_id"] or b.get("name") == best["buyer_name"]),
            None
        )

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

    buyer_label = selected_buyer.get("name") or selected_buyer.get("buyer_name") or "Unknown Buyer"
    logs.append(
        f"🎯 [Matching Engine] Matched: {buyer_label} "
        f"(Target ₹{selected_buyer.get('target_price')}/kg)"
    )

    initial_buyer_offer = round(selected_buyer.get("target_price", state["min_price"]) * 0.75, 2)
    initial_farmer_ask = round(state["min_price"] * 1.2, 2)

    return {
        "buyer_profile": selected_buyer,
        "selected_buyer": selected_buyer,
        "latest_buyer_offer": initial_buyer_offer,
        "latest_farmer_ask": initial_farmer_ask,
        "market_offers": market_offers,
        "logs": logs,
    }


# ─────────────────────────────────────────────
# Node 4: Farmer Agent
# ─────────────────────────────────────────────

async def farmer_node(state: NegotiationState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    history = list(state.get("history", []))
    current_round = state.get("round", 0) + 1

    buyer_offer = state.get("latest_buyer_offer") or round(
        state.get("buyer_profile", {}).get("target_price", state["min_price"]) * 0.75, 2
    )
    farmer_ask = state.get("latest_farmer_ask") or round(state["min_price"] * 1.2, 2)

    logs.append(
        f"👨‍🌾 [Farmer] Round {current_round}: Buyer offered ₹{buyer_offer}/kg | My ask ₹{farmer_ask}/kg"
    )

    # 1. Accept check: buyer meets farmer within 2%
    if buyer_offer >= farmer_ask * 0.98:
        logs.append(f"👨‍🌾 [Farmer] ACCEPTED buyer offer ₹{buyer_offer}/kg.")
        return {"status": "DEAL", "round": current_round, "latest_farmer_ask": buyer_offer, "logs": logs}

    # 2. Critical spoilage override
    if state["spoilage_days"] <= 2:
        logs.append("⚠️ [Farmer] Spoilage critical. Accepting near-min or escalating.")
        if buyer_offer >= state["min_price"] * 0.85:
            return {"status": "DEAL", "round": current_round, "latest_farmer_ask": buyer_offer, "logs": logs}
        return {"status": "REJECT", "round": current_round, "logs": logs}

    # 3. Try LLM structured decision via FARMER_PROMPT
    decision = None
    prompt = FARMER_PROMPT.format(
        crop=state["crop"],
        quantity=state["quantity"],
        min_price=state["min_price"],
        location=state["location"],
        shelf_life=state["spoilage_days"],
        market_price=state["market_price"],
        buyer_offer=buyer_offer,
        round=current_round,
        history=_format_history(history),
        rag_context=state.get("rag_context", "No context available.")
    )
    raw = llm_client.generate(prompt, max_tokens=120, temperature=0.3)
    decision = _parse_json_response(raw)

    # 4. LLM decision valid — apply it
    if decision and decision.get("decision") in ("ACCEPT", "COUNTER", "REJECT"):
        agent_decision = decision["decision"]
        counter = decision.get("counter_price")
        reason = decision.get("reason", "")
        logs.append(f"👨‍🌾 [Farmer][LLM] {agent_decision}: {reason[:80]}")

        if agent_decision == "ACCEPT":
            return {"status": "DEAL", "round": current_round, "latest_farmer_ask": buyer_offer, "logs": logs}
        if agent_decision == "REJECT":
            return {"status": "REJECT", "round": current_round, "logs": logs}
        # COUNTER — validate counter price
        if counter and isinstance(counter, (int, float)):
            counter = max(float(state["min_price"]), min(float(farmer_ask), float(counter)))
            counter = round(counter, 2)
        else:
            # Fall through to deterministic
            decision = None

    # 5. Deterministic fallback concession (20% of gap toward buyer)
    if not decision or not decision.get("counter_price"):
        gap = farmer_ask - buyer_offer
        concession = (gap * 0.2) + random.uniform(0.1, 0.4)
        counter = round(buyer_offer + concession, 2)
        counter = max(float(state["min_price"]), counter)
        if counter >= farmer_ask:
            counter = round(farmer_ask - 0.5, 2)
        counter = max(float(state["min_price"]), counter)

    # Fast-accept: if counter is within 2% of buyer offer just accept
    if buyer_offer >= counter * 0.98:
        logs.append(f"👨‍🌾 [Farmer] Counter ₹{counter}/kg close enough — accepting ₹{buyer_offer}/kg.")
        return {"status": "DEAL", "round": current_round, "latest_farmer_ask": buyer_offer, "logs": logs}

    logs.append(f"👨‍🌾 [Farmer] Counter ask: ₹{counter}/kg.")
    history.append({
        "round": current_round,
        "agent": "Farmer",
        "price": counter,
        "decision": "COUNTER",
        "quantity": state["quantity"],
        "message": "Counter-offer from farmer."
    })

    return {
        "round": current_round,
        "history": history,
        "latest_farmer_ask": counter,
        "latest_buyer_offer": buyer_offer,
        "logs": logs,
    }


# ─────────────────────────────────────────────
# Node 5: Buyer Agent
# ─────────────────────────────────────────────

async def buyer_node(state: NegotiationState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    history = list(state.get("history", []))
    current_round = state.get("round", 0)

    farmer_ask = state.get("latest_farmer_ask", round(state["min_price"] * 1.2, 2))
    buyer_profile = state["buyer_profile"]
    buyer_offer = state.get("latest_buyer_offer") or round(
        buyer_profile.get("target_price", state["min_price"]) * 0.75, 2
    )

    logs.append(
        f"🤝 [Buyer] Round {current_round}: Farmer asks ₹{farmer_ask}/kg | My bid ₹{buyer_offer}/kg"
    )

    # 1. Accept: farmer ask within 3% of target
    target_threshold = buyer_profile.get("target_price", state["min_price"]) * 1.03
    if farmer_ask <= target_threshold:
        logs.append(f"🤝 [Buyer] ACCEPTED farmer ask ₹{farmer_ask}/kg.")
        return {"status": "DEAL", "latest_buyer_offer": farmer_ask, "logs": logs}

    # 2. LLM structured decision via BUYER_PROMPT
    decision = None
    prompt = BUYER_PROMPT.format(
        buyer_name=buyer_profile.get("name", "Buyer"),
        target_price=buyer_profile.get("target_price", state["min_price"]),
        budget=buyer_profile.get("budget", 100000),
        max_quantity=buyer_profile.get("max_quantity", state["quantity"]),
        location=buyer_profile.get("location", state["location"]),
        farmer_ask=farmer_ask,
        round=current_round,
        history=_format_history(history),
        rag_context=state.get("rag_context", "No context available.")
    )
    raw = llm_client.generate(prompt, max_tokens=120, temperature=0.3)
    decision = _parse_json_response(raw)

    if decision and decision.get("decision") in ("ACCEPT", "COUNTER", "REJECT"):
        agent_decision = decision["decision"]
        counter = decision.get("counter_price")
        reason = decision.get("reason", "")
        logs.append(f"🤝 [Buyer][LLM] {agent_decision}: {reason[:80]}")

        if agent_decision == "ACCEPT":
            return {"status": "DEAL", "latest_buyer_offer": farmer_ask, "logs": logs}
        if agent_decision == "REJECT":
            return {"status": "REJECT", "logs": logs}
        if counter and isinstance(counter, (int, float)):
            max_viable = float(buyer_profile.get("budget", 100000)) / state["quantity"]
            counter = min(max_viable, float(farmer_ask), float(counter))
            counter = max(float(buyer_offer), counter)
            counter = round(counter, 2)
        else:
            decision = None

    # 3. Deterministic fallback (20% concession toward farmer)
    if not decision or not decision.get("counter_price"):
        gap = farmer_ask - buyer_offer
        concession = (gap * 0.2) + random.uniform(0.1, 0.4)
        counter = round(buyer_offer + concession, 2)
        counter = min(farmer_ask, counter)
        if counter <= buyer_offer:
            counter = round(buyer_offer + 0.5, 2)
        max_viable = float(buyer_profile.get("budget", 100000)) / state["quantity"]
        counter = min(max_viable, counter)

    # Fast-accept if counter nearly meets farmer ask
    if farmer_ask <= counter * 1.03:
        logs.append(f"🤝 [Buyer] Counter ₹{counter}/kg close enough — accepting ₹{farmer_ask}/kg.")
        return {"status": "DEAL", "latest_buyer_offer": farmer_ask, "logs": logs}

    logs.append(f"🤝 [Buyer] Counter bid: ₹{counter}/kg.")
    history.append({
        "round": current_round,
        "agent": "Buyer",
        "price": counter,
        "decision": "COUNTER",
        "quantity": state["quantity"],
        "message": "Counter-offer from buyer."
    })

    return {
        "history": history,
        "latest_buyer_offer": counter,
        "logs": logs,
    }


# ─────────────────────────────────────────────
# Node 6: Validator
# ─────────────────────────────────────────────

async def validator_node(state: NegotiationState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    logs.append("⚖️ [Validator] Validating deal constraints.")

    deal_price = state.get("latest_buyer_offer", 0)
    budget = state["buyer_profile"].get("budget", 100000)
    total_cost = deal_price * state["quantity"]

    valid = True
    reason = "All validation checks passed."

    if total_cost > budget:
        valid = False
        reason = f"Budget exceeded: ₹{total_cost:.2f} > Buyer budget ₹{budget:.2f}"
    elif deal_price < state["min_price"] and state["spoilage_days"] > 2:
        valid = False
        reason = f"Price ₹{deal_price} below minimum ₹{state['min_price']} and spoilage not critical."

    logs.append(f"⚖️ [Validator] Valid={valid}. {reason}")

    if valid:
        deal = {
            "buyer_name": state["buyer_profile"]["name"],
            "buyer_id": state["buyer_profile"]["id"],
            "price": deal_price,
            "quantity": state["quantity"],
            "total_value": round(deal_price * state["quantity"], 2),
            "status": "DEAL",
        }
        return {"status": "DEAL", "deal": deal, "logs": logs}
    else:
        return {"status": "REJECT", "logs": logs}


# ─────────────────────────────────────────────
# Node 7: Reflection + Supply Chain Fallback
# ─────────────────────────────────────────────

async def reflection_node(state: NegotiationState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    logs.append("🧐 [Reflection] Post-negotiation analysis started.")

    history_str = _format_history(state.get("history", []))
    final_price = state.get("latest_buyer_offer", 0)

    prompt = REFLECTION_PROMPT.format(
        crop=state["crop"],
        status=state["status"],
        rounds=state["round"],
        history=history_str,
        summary=f"Status: {state['status']}. Final price considered: ₹{final_price}/kg.",
        market_price=state["market_price"],
        final_price=final_price
    )

    reflection_text = llm_client.generate(prompt, max_tokens=180)
    if not reflection_text:
        reflection_text = (
            f"The {state['crop']} negotiation ended with status {state['status']} "
            f"after {state['round']} rounds. "
            f"Final price ₹{final_price}/kg vs market ₹{state['market_price']}/kg."
        )

    logs.append(f"🧐 [Reflection] {reflection_text.strip()[:120]}...")

    # Write to ChromaDB strategies_index
    try:
        from backend.services.rag_service import rag_service
        from uuid import uuid4
        log_id = str(uuid4())
        await rag_service.add_strategy_log(
            log_id=log_id,
            text=reflection_text.strip(),
            metadata={
                "crop": state["crop"],
                "status": state["status"],
                "rounds": state["round"],
                "market_price": state["market_price"],
                "final_price": final_price,
            }
        )
        logs.append("🧐 [Reflection] Strategy log written to ChromaDB.")
    except Exception as e:
        logger.warning(f"ChromaDB strategy write failed: {e}")

    # ── Supply chain fallbacks if no deal ──
    final_status = state["status"]
    deal = state.get("deal")

    if final_status != "DEAL":
        logs.append("⚠️ [Reflection] Direct sale failed. Evaluating supply chain fallbacks.")
        spoilage = state["spoilage_days"]
        storage_cost = 1.8 * state["quantity"] * spoilage

        if spoilage > 2 and storage_cost < state["market_price"] * state["quantity"] * 0.3:
            logs.append("🏗️ [Reflection] Fallback: STORAGE")
            final_status = "ESCALATED_STORAGE"
            deal = {
                "type": "STORAGE",
                "price": round(state["market_price"] * 0.9, 2),
                "quantity": state["quantity"],
                "warehouse": "WarehouseAgent",
                "storage_cost": round(storage_cost, 2),
            }
        elif state["market_price"] * 0.8 >= state["min_price"] * 0.6:
            logs.append("⚙️ [Reflection] Fallback: PROCESSING")
            final_status = "ESCALATED_PROCESSING"
            deal = {
                "type": "PROCESSING",
                "price": round(state["market_price"] * 0.8, 2),
                "quantity": state["quantity"],
                "processor": "ProcessorAgent",
            }
        else:
            logs.append("♻️ [Reflection] Fallback: COMPOSTING")
            final_status = "ESCALATED_COMPOST"
            deal = {
                "type": "COMPOST",
                "price": 8.0,
                "quantity": state["quantity"],
                "compost": "CompostAgent",
            }

    # Recommendation analysis
    recommendation = _generate_recommendation(state, deal)

    return {
        "status": final_status,
        "deal": deal,
        "reflection": reflection_text.strip(),
        "recommendation": recommendation,
        "logs": logs,
    }


async def _generate_recommendation(state: NegotiationState, deal: Optional[Dict]) -> str:
    """Generate a farmer recommendation based on deal outcome."""
    try:
        from backend.agents.prompts import RECOMMENDATION_PROMPT
        deal_type = deal.get("type", "DIRECT") if deal else "NONE"
        prompt = RECOMMENDATION_PROMPT.format(
            crop=state["crop"],
            quantity=state["quantity"],
            farmer_min_price=state["min_price"],
            direct_sale_result=f"Status={state['status']}, Price=₹{state.get('latest_buyer_offer', 0)}/kg",
            storage_cost=round(1.8 * state["quantity"] * state["spoilage_days"], 2),
            storage_days=state["spoilage_days"],
            processor_offer=round(state["market_price"] * 0.8, 2),
            market_price=state["market_price"]
        )
        rec = llm_client.generate(prompt, max_tokens=120)
        if rec:
            return rec.strip()
    except Exception as e:
        logger.warning(f"Recommendation generation failed: {e}")

    # Deterministic fallback
    if deal and deal.get("type") == "DIRECT" or state["status"] == "DEAL":
        return f"Direct sale at ₹{state.get('latest_buyer_offer', state['min_price'])}/kg is the optimal outcome."
    elif state["spoilage_days"] > 2:
        return f"Store in cold warehouse — market price may recover in {state['spoilage_days']} days."
    return f"Consider processing or composting to recover value from the {state['crop']} lot."


# ─────────────────────────────────────────────
# Conditional Routing
# ─────────────────────────────────────────────

async def route_after_farmer(state: NegotiationState) -> str:
    if state["status"] in ("DEAL", "ACCEPT"):
        return "validator_agent"
    if state["status"] == "REJECT" or state["round"] >= state["max_rounds"]:
        return "reflection_agent"
    return "buyer_agent"


async def route_after_buyer(state: NegotiationState) -> str:
    if state["status"] in ("DEAL", "ACCEPT"):
        return "validator_agent"
    if state["status"] == "REJECT" or state["round"] >= state["max_rounds"]:
        return "reflection_agent"
    return "farmer_agent"


async def route_after_validator(state: NegotiationState) -> str:
    return "reflection_agent"


# ─────────────────────────────────────────────
# Compile LangGraph State Machine
# ─────────────────────────────────────────────

workflow = StateGraph(NegotiationState)

workflow.add_node("planner_agent", planner_node)
workflow.add_node("market_intelligence_agent", market_intelligence_node)
workflow.add_node("matching_agent", matching_engine_node)
workflow.add_node("farmer_agent", farmer_node)
workflow.add_node("buyer_agent", buyer_node)
workflow.add_node("validator_agent", validator_node)
workflow.add_node("reflection_agent", reflection_node)

workflow.set_entry_point("planner_agent")

workflow.add_edge("planner_agent", "market_intelligence_agent")
workflow.add_edge("market_intelligence_agent", "matching_agent")
workflow.add_edge("matching_agent", "farmer_agent")

workflow.add_conditional_edges(
    "farmer_agent",
    route_after_farmer,
    {
        "validator_agent": "validator_agent",
        "reflection_agent": "reflection_agent",
        "buyer_agent": "buyer_agent",
    }
)

workflow.add_conditional_edges(
    "buyer_agent",
    route_after_buyer,
    {
        "validator_agent": "validator_agent",
        "reflection_agent": "reflection_agent",
        "farmer_agent": "farmer_agent",
    }
)

workflow.add_conditional_edges(
    "validator_agent",
    route_after_validator,
    {"reflection_agent": "reflection_agent"}
)

workflow.add_edge("reflection_agent", END)

graph_orchestrator = workflow.compile()
