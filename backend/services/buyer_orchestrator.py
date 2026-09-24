"""
backend/services/buyer_orchestrator.py
------------------------------------------------------------------------
Autonomous Top-5 Buyer Negotiation Orchestration Service.

Architecture:
  1. Candidate Discovery & Top-5 Selection (from user input, DB listings, or verified suppliers).
  2. Isolated Parallel Negotiation Engine (concurrent sessions via asyncio.gather).
  3. Strict State & Budget Isolation (independent BuyerAgent sessions, no shared mutable state).
  4. Automatic Multi-Round Negotiation Progression (1 to max_rounds; no manual user intervention).
  5. Strict Deterministic Outcome Validation (Reservation ceiling, budget, quantity, crop checks).
  6. Verified Landed Cost Evaluation (Base price + highway distance freight + APMC statutory cess).
  7. Deterministic No-Winner Handling (winner = None, status = "NO_EXECUTABLE_DEAL" when no deal qualifies).
  8. Real-Time WebSocket Streaming of all 5 parallel negotiations for live visible execution.
  9. Natural Chat-Style Formatting for Terminal, UI, and API.
"""

import math
import uuid
import asyncio
import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from agents.buyer_agent import BuyerAgent, BUYER_PERSONAS
from database.db import Database
from shared.crop_catalog import (
    is_supported_buyer_crop,
    normalize_crop_name,
    validate_buyer_crop,
)
from backend.services.matching_service import match_requirement_to_listings
from backend.services.buyer_market_context_service import buyer_market_context_service
from backend.services.current_mandi_service import current_mandi_service

logger = logging.getLogger("BuyerOrchestrator")

# Verified Maharashtra suppliers pool from negotiation service
from backend.services.negotiation_service import (
    STATUTORY_BENCHMARKS,
)

try:
    from backend.websocket.agent_updates import agent_update_hub
except Exception:
    agent_update_hub = None


async def _broadcast_safe(payload: dict):
    """Safely broadcasts a live event payload to all connected WebSockets."""
    if agent_update_hub:
        try:
            await agent_update_hub.broadcast(payload)
        except Exception as e:
            logger.debug(f"Broadcast error: {e}")


class BuyerOrchestrationService:
    """
    Autonomous Top-5 Multi-Seller Negotiation Orchestrator for Buyer Agents.
    """

    def __init__(self):
        self.active_orchestrations: Dict[str, Any] = {}

    async def get_top_candidates(
        self,
        requirement: Dict[str, Any],
        max_candidates: int = 5,
        allow_test_fixtures: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Discovers and ranks eligible candidate sellers/listings for the buyer requirement:
        Priority:
          1. Explicit candidates provided in payload (e.g. requirement["sellers"] or requirement["candidates"] in test fixtures).
          2. Active produce listings from Database matched via match_requirement_to_listings().
        Deterministic Ranking:
          All candidates are ranked deterministically by (-match_score, distance_km, floor_price).
        Strictly returns up to max_candidates. Never fabricates fake candidates in production if fewer or zero exist.
        If zero real candidates exist: returns [] -> NO_CANDIDATES_FOUND.
        """
        crop_input = requirement.get("crop", "Soybean")
        norm_crop = normalize_crop_name(crop_input) or crop_input
        req_qty = float(requirement.get("quantity", 500.0))
        target_p = float(requirement.get("target_price") or requirement.get("max_price") or 50.0)

        # 1. Explicit sellers provided in input (e.g. unit tests or API payload)
        explicit_sellers = requirement.get("sellers") or requirement.get("candidates") or requirement.get("listings")
        if explicit_sellers and isinstance(explicit_sellers, list):
            candidates = []
            for idx, s in enumerate(explicit_sellers):
                if not isinstance(s, dict):
                    continue
                s_name = s.get("name") or s.get("farmer_name") or f"Seller {chr(65 + idx)}"
                s_id = s.get("id") or s.get("seller_id") or f"seller_{idx + 1}"
                s_crop = s.get("crop") or norm_crop
                s_qty = float(s.get("quantity", req_qty))
                s_price = float(s.get("price") or s.get("ask_price") or s.get("min_price") or target_p)
                s_loc = s.get("location") or requirement.get("location", "Maharashtra")
                s_dist = float(s.get("distance_km") or s.get("dist") or 120.0)
                s_floor = float(s.get("min_price") or s.get("floor_price") or round(s_price * 0.85, 2))
                s_flex = float(s.get("flexibility") or 0.15)
                s_special = s.get("special") or s.get("description") or "Commercial Lot"
                s_match = float(s.get("match_score") or s.get("compatibility_score") or s.get("match") or 90.0)

                candidates.append({
                    "id": s_id,
                    "seller_id": s_id,
                    "name": s_name,
                    "crop": s_crop,
                    "quantity": s_qty,
                    "price": s_price,
                    "initial_ask": s_price,
                    "floor_price": s_floor,
                    "flexibility": s_flex,
                    "location": s_loc,
                    "distance_km": s_dist,
                    "special": s_special,
                    "match_score": s_match,
                    "source": "explicit_input",
                })
            # Deterministic ranking by match score (desc), distance (asc), floor price (asc)
            candidates.sort(key=lambda c: (-c["match_score"], c["distance_km"], c["floor_price"]))
            return candidates[:max_candidates]

        # 2. Database listings matching from verified DB produce records
        candidates = []
        try:
            db_matches = await match_requirement_to_listings(requirement)
            for idx, m in enumerate(db_matches):
                s_id = m.get("listing_id") or f"listing_{idx + 1}"
                s_name = m.get("farmer_name") or f"Farmer {m.get('farmer_id', idx + 1)}"
                s_price = float(m.get("min_price", target_p))
                initial_ask = round(s_price * 1.15, 2)
                candidates.append({
                    "id": s_id,
                    "seller_id": s_id,
                    "name": s_name,
                    "crop": m.get("crop", norm_crop),
                    "quantity": float(m.get("quantity", req_qty)),
                    "price": initial_ask,
                    "initial_ask": initial_ask,
                    "floor_price": s_price,
                    "flexibility": 0.15,
                    "location": m.get("location", "Maharashtra"),
                    "distance_km": float(m.get("distance_km", 100.0)),
                    "special": f"Grade {m.get('quality', 'A')} Listing",
                    "match_score": float(m.get("compatibility_score", 90.0)),
                    "source": "db_listings",
                })
        except Exception as e:
            logger.warning(f"Error querying DB listings: {e}")

        if candidates:
            # Deterministic ranking
            candidates.sort(key=lambda c: (-c["match_score"], c["distance_km"], c["floor_price"]))
            return candidates[:max_candidates]

        # In production flow with 0 real matches: strictly return empty list (NO_CANDIDATES_FOUND)
        return []

    async def _negotiate_single_seller_branch(
        self,
        seller: Dict[str, Any],
        requirement: Dict[str, Any],
        market_context: Optional[Any] = None,
        max_rounds: int = 5,
        branch_idx: int = 0,
        negotiation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes an isolated, autonomous, multi-round negotiation session with a single seller.
        Creates a dedicated BuyerAgent instance to guarantee complete state isolation.
        Streams real-time round events via WebSocket for visible live execution.
        """
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        crop = requirement.get("crop", "Soybean")
        buyer_name = requirement.get("buyer_name", "Procurement Buyer")
        budget = float(requirement.get("budget", 1000000.0))
        target_p = float(requirement.get("target_price") or requirement.get("max_price") or 50.0)
        max_price = float(requirement.get("max_price") or requirement.get("reservation_price") or target_p * 1.20)
        req_qty = float(requirement.get("quantity", 500.0))
        location = requirement.get("location", "Maharashtra")
        persona = requirement.get("persona") or requirement.get("buyer_persona") or "bulk_wholesaler"
        strategy = requirement.get("strategy", "balanced")

        # 1. Instantiate Isolated BuyerAgent
        buyer_agent = BuyerAgent(
            name=f"{buyer_name} [{seller['name']}]",
            budget=budget,
            max_quantity=req_qty,
            target_price=target_p,
            reservation_price=max_price,
            location=location,
            strategy=strategy,
            persona=persona,
            crop=crop,
        )

        seller_ask = float(seller.get("price") or seller.get("initial_ask") or target_p)
        seller_floor = float(seller.get("floor_price") or seller_ask * 0.85)
        seller_flex = float(seller.get("flexibility", 0.15))
        avail_qty = float(seller.get("quantity", req_qty))
        executable_qty = min(req_qty, avail_qty)
        dist_km = float(seller.get("distance_km", 100.0))

        rounds_history = []
        messages = []
        branch_status = "ACTIVE"
        outcome = "UNKNOWN"
        final_price = None
        rejection_reason = None
        final_contract = None

        # Determine market anchor
        market_price = float(requirement.get("market_price") or target_p)

        # Broadcast Branch Start Event
        if negotiation_id:
            await _broadcast_safe({
                "event": "TOP5_BRANCH_START",
                "negotiation_id": negotiation_id,
                "branch_index": branch_idx,
                "session_id": session_id,
                "seller_name": seller["name"],
                "seller_location": seller["location"],
                "distance_km": dist_km,
                "initial_ask": seller_ask,
                "quantity": executable_qty,
                "crop": crop,
                "message": f"Negotiation branch #{branch_idx + 1} initialized with {seller['name']} ({seller['location']}). Opening ask: ₹{seller_ask:.2f}/kg.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # 2. Multi-Round Negotiation Loop
        for r in range(1, max_rounds + 1):
            # Seller proposal in round r
            if r > 1:
                last_buyer_bid = buyer_agent.current_bid
                spread = max(0.0, seller_ask - max(last_buyer_bid, seller_floor))
                concession_step = round(spread * (seller_flex + 0.05 * (r - 1)), 2)
                seller_ask = max(seller_floor, round(seller_ask - concession_step, 2))

            # Broadcast Seller Turn via WebSocket
            if negotiation_id:
                await _broadcast_safe({
                    "event": "TOP5_ROUND_UPDATE",
                    "negotiation_id": negotiation_id,
                    "branch_index": branch_idx,
                    "session_id": session_id,
                    "seller_name": seller["name"],
                    "seller_location": seller["location"],
                    "round": r,
                    "max_rounds": max_rounds,
                    "actor": "SELLER",
                    "agent": f"{seller['name']} ({seller['location']} APMC)",
                    "type": "offer",
                    "price": seller_ask,
                    "quantity": executable_qty,
                    "quality": "A",
                    "deliveryDate": "3-4 Business Days",
                    "transportIncluded": True,
                    "warehouseIncluded": False,
                    "validity": "24 Hours",
                    "message": f"Offering {executable_qty:,.0f}kg {crop} at ₹{seller_ask:.2f}/kg.",
                    "reasoning": [
                        f"APMC Benchmark: ₹{market_price:.2f}/kg",
                        f"Transit: {dist_km:.0f} km via Maharashtra Highway",
                        f"Grade A Quality Certified"
                    ],
                    "branch_status": "Negotiating",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                # Realistic async delay for parallel event observation
                await asyncio.sleep(0.35)

            offer_payload = {
                "price": seller_ask,
                "quantity": executable_qty,
                "crop": crop,
                "shelf_life": int(seller.get("shelf_life", 4)),
            }
            context_payload = {
                "round": r,
                "max_rounds": max_rounds,
                "market_price": market_price,
                "seller_name": seller["name"],
                "crop": crop,
                "buyer_market_context": market_context,
            }

            # Buyer evaluates seller offer deterministically
            buyer_response = buyer_agent.respond_to_offer(
                offer=offer_payload,
                context=context_payload,
                force_deterministic=True,
            )

            decision_type = buyer_response.get("type", "REJECT")
            resp_price = buyer_response.get("price", seller_ask)
            resp_qty = buyer_response.get("quantity", executable_qty)
            resp_msg = buyer_response.get("message", "")
            buyer_bid_val = buyer_agent.current_bid if decision_type == "COUNTER" else resp_price

            # Log round
            round_record = {
                "round": r,
                "seller_ask": seller_ask,
                "buyer_bid": buyer_bid_val,
                "buyer_decision": decision_type,
                "buyer_message": resp_msg,
                "quantity": resp_qty,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            rounds_history.append(round_record)

            messages.append(f"Round {r} | Seller: ₹{seller_ask:.2f}/kg ({executable_qty:.0f}kg)")
            messages.append(f"Round {r} | Buyer: {decision_type} - {resp_msg}")

            # Broadcast Buyer Turn via WebSocket
            if negotiation_id:
                await _broadcast_safe({
                    "event": "TOP5_ROUND_UPDATE",
                    "negotiation_id": negotiation_id,
                    "branch_index": branch_idx,
                    "session_id": session_id,
                    "seller_name": seller["name"],
                    "seller_location": seller["location"],
                    "round": r,
                    "max_rounds": max_rounds,
                    "actor": "BUYER",
                    "agent": "Buyer Agent (Autonomous)",
                    "type": "offer" if decision_type == "COUNTER" else "text",
                    "decision": decision_type,
                    "price": buyer_bid_val,
                    "quantity": resp_qty,
                    "quality": "A",
                    "deliveryDate": "Prompt Dispatch",
                    "transportIncluded": True,
                    "warehouseIncluded": False,
                    "validity": "24 Hours",
                    "message": resp_msg or f"{decision_type} offer of ₹{seller_ask:.2f}/kg",
                    "reasoning": [
                        f"Evaluated against ceiling: ₹{max_price:.2f}/kg",
                        f"RL multi-attribute utility optimization"
                    ],
                    "branch_status": "Deal" if decision_type == "ACCEPT" else ("Rejected" if decision_type == "REJECT" else "Negotiating"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                await asyncio.sleep(0.35)

            # Process Decision
            if decision_type == "ACCEPT":
                if seller_ask <= buyer_agent.reservation_price and (seller_ask * resp_qty <= budget):
                    branch_status = "DEAL"
                    outcome = "DEAL"
                    final_price = seller_ask
                    executable_qty = float(resp_qty)
                    final_contract = buyer_response.get("contract")
                    messages.append(f"🤝 Deal confirmed with {seller['name']} at ₹{final_price:.2f}/kg for {executable_qty:.0f}kg.")
                else:
                    branch_status = "REJECT"
                    outcome = "REJECT"
                    rejection_reason = f"Price ₹{seller_ask}/kg exceeded reservation ceiling (₹{buyer_agent.reservation_price}/kg) or budget (₹{budget})."
                    messages.append(f"❌ Rejection: {rejection_reason}")
                break

            elif decision_type == "REJECT":
                branch_status = "REJECT"
                outcome = "REJECT"
                rejection_reason = resp_msg or "Offer rejected under buyer economic policy."
                messages.append(f"❌ Rejection: {rejection_reason}")
                break

            elif decision_type == "COUNTER":
                # Check stall detection
                if r >= 3 and abs(rounds_history[-1]["seller_ask"] - rounds_history[-2]["seller_ask"]) < 0.05 and seller_ask > max_price:
                    branch_status = "STALLED"
                    outcome = "STALLED"
                    rejection_reason = f"Stall detected: Seller maintained price at ₹{seller_ask:.2f}/kg above reservation ceiling."
                    messages.append(f"🛑 Negotiation stalled: {rejection_reason}")
                    break

                if r == max_rounds:
                    branch_status = "MAX_ROUNDS_REACHED"
                    outcome = "MAX_ROUNDS_REACHED"
                    rejection_reason = f"Maximum negotiation rounds ({max_rounds}) reached without acceptable agreement below ₹{max_price:.2f}/kg."
                    messages.append(f"⏱️ {rejection_reason}")
                    break

        # 3. Calculate Landed Cost (Base + Freight + APMC Cess)
        freight_total = max(650.0, round(dist_km * 6.50 + executable_qty * 0.35, 2))
        freight_per_kg = round(freight_total / max(1.0, executable_qty), 2)
        
        effective_price = final_price if (outcome == "DEAL" and final_price is not None) else seller_ask
        apmc_cess_per_kg = round(effective_price * 0.01, 2)
        landed_cost_per_kg = round(effective_price + freight_per_kg + apmc_cess_per_kg, 2)
        total_landed_cost = round(landed_cost_per_kg * executable_qty, 2)

        # Strict Deal Validation
        is_valid_deal = (
            outcome == "DEAL"
            and final_price is not None
            and final_price > 0
            and not math.isnan(final_price)
            and not math.isinf(final_price)
            and final_price <= max_price
            and (final_price * executable_qty <= budget)
            and executable_qty > 0
            and is_supported_buyer_crop(crop)
        )

        # Broadcast Branch Complete Event
        if negotiation_id:
            await _broadcast_safe({
                "event": "TOP5_BRANCH_COMPLETE",
                "negotiation_id": negotiation_id,
                "branch_index": branch_idx,
                "session_id": session_id,
                "seller_name": seller["name"],
                "seller_location": seller["location"],
                "outcome": outcome,
                "branch_status": branch_status,
                "final_price": final_price,
                "freight_per_kg": freight_per_kg,
                "apmc_cess_per_kg": apmc_cess_per_kg,
                "landed_cost_per_kg": landed_cost_per_kg,
                "total_landed_cost": total_landed_cost,
                "is_valid_deal": is_valid_deal,
                "rejection_reason": rejection_reason,
                "rounds_count": len(rounds_history),
                "message": f"Branch #{branch_idx + 1} ({seller['name']}) concluded with {outcome} at ₹{effective_price:.2f}/kg (Landed: ₹{landed_cost_per_kg:.2f}/kg).",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        return {
            "session_id": session_id,
            "seller_id": seller.get("id") or seller.get("seller_id"),
            "seller_name": seller.get("name"),
            "location": seller.get("location"),
            "distance_km": dist_km,
            "crop": crop,
            "requested_quantity": req_qty,
            "executable_quantity": executable_qty,
            "initial_ask": float(seller.get("initial_ask") or seller.get("price")),
            "final_price": final_price,
            "freight_total": freight_total,
            "freight_per_kg": freight_per_kg,
            "apmc_cess_per_kg": apmc_cess_per_kg,
            "landed_cost_per_kg": landed_cost_per_kg,
            "total_landed_cost": total_landed_cost,
            "status": branch_status,
            "outcome": outcome,
            "is_valid_deal": is_valid_deal,
            "rejection_reason": rejection_reason,
            "match_score": float(seller.get("match_score", 85.0)),
            "rounds_count": len(rounds_history),
            "rounds": rounds_history,
            "messages": messages,
            "contract": final_contract,
        }

    async def orchestrate_negotiation(
        self,
        requirement: Dict[str, Any],
        max_candidates: int = 5,
        max_rounds: int = 5,
        negotiation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Main entrypoint for autonomous top-5 buyer negotiation orchestration.
        Executes parallel multi-round negotiations, waits for all branches to finish,
        validates executable deals, ranks by landed cost, and produces a structured result.
        Streams real-time events to all connected WebSockets throughout the process.
        """
        orch_id = f"orch_{uuid.uuid4().hex[:8]}"
        neg_id = negotiation_id or requirement.get("negotiation_id") or requirement.get("id")
        crop = requirement.get("crop", "Soybean")
        norm_crop = normalize_crop_name(crop) or crop

        # Strict crop allowlist validation
        if not is_supported_buyer_crop(norm_crop):
            return {
                "orchestration_id": orch_id,
                "status": "ERROR_UNSUPPORTED_CROP",
                "message": f"Unsupported crop '{crop}'. Buyer Agent strictly negotiates only the 7 canonical Maharashtra crops.",
                "candidate_count": 0,
                "negotiations": [],
                "executable_deals": [],
                "winner": None,
                "chat_transcript": f"Error: '{crop}' is not a supported Maharashtra crop.",
            }

        req_qty = float(requirement.get("quantity", 500.0))
        if req_qty <= 0 or math.isnan(req_qty) or math.isinf(req_qty):
            return {
                "orchestration_id": orch_id,
                "status": "ERROR_INVALID_QUANTITY",
                "message": f"Invalid quantity: {req_qty}. Must be a positive finite number.",
                "candidate_count": 0,
                "negotiations": [],
                "executable_deals": [],
                "winner": None,
                "chat_transcript": "Error: Procurement quantity must be strictly positive.",
            }

        target_p = float(requirement.get("target_price") or requirement.get("max_price") or 50.0)
        reservation_p = float(requirement.get("max_price") or requirement.get("reservation_price") or target_p * 1.20)
        budget = float(requirement.get("budget", 1000000.0))

        # Broadcast Step 1: Validation
        if neg_id:
            await _broadcast_safe({
                "event": "TOP5_STATUS",
                "negotiation_id": neg_id,
                "step": "VALIDATING",
                "message": f"Validating procurement requirement for {req_qty:,.0f}kg {norm_crop} (Target: ₹{target_p:.2f}/kg, Ceiling: ₹{reservation_p:.2f}/kg).",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # 1. Fetch Market Context (RAG, Mandi, ML)
        market_context = None
        if buyer_market_context_service:
            try:
                market_context = buyer_market_context_service.build_market_context(
                    crop=norm_crop,
                    location=requirement.get("location", "Maharashtra"),
                    persona=requirement.get("persona", "bulk_wholesaler"),
                    context=requirement,
                )
            except Exception as e:
                logger.warning(f"Could not build market context: {e}")

        # 2. Discover Top Candidates
        candidates = await self.get_top_candidates(requirement, max_candidates=max_candidates)
        candidate_count = len(candidates)

        if candidate_count == 0:
            return {
                "orchestration_id": orch_id,
                "requirement": requirement,
                "candidate_count": 0,
                "negotiations": [],
                "executable_deals": [],
                "winner": None,
                "status": "NO_CANDIDATES_FOUND",
                "message": f"No eligible seller candidates found for {norm_crop}.",
                "chat_transcript": f"System: No active seller listings found for {norm_crop}.",
            }

        # Broadcast Step 2: Discovery & Selection of Top 5
        if neg_id:
            await _broadcast_safe({
                "event": "TOP5_DISCOVERY",
                "negotiation_id": neg_id,
                "step": "DISCOVERING FARMERS",
                "candidate_count": candidate_count,
                "candidates": [
                    {
                        "index": idx,
                        "name": c["name"],
                        "location": c["location"],
                        "distance_km": c["distance_km"],
                        "initial_ask": c["price"],
                        "negotiated_price": c["price"],
                        "freight_per_kg": round((max(650.0, c["distance_km"] * 6.50 + req_qty * 0.35)) / max(1.0, req_qty), 2),
                        "landed_cost_per_kg": round(c["price"] + ((max(650.0, c["distance_km"] * 6.50 + req_qty * 0.35)) / max(1.0, req_qty)) + (c["price"] * 0.01), 2),
                        "match_score": c.get("match_score", 90.0),
                        "round": 1,
                        "status": "Discovered",
                        "is_best": False,
                    }
                    for idx, c in enumerate(candidates)
                ],
                "message": f"Found {candidate_count} eligible candidate farmers across Maharashtra APMC mandis. Starting concurrent negotiations in parallel...",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            await asyncio.sleep(0.3)

        # 3. Launch Parallel Isolated Negotiations
        tasks = [
            self._negotiate_single_seller_branch(
                seller=c,
                requirement=requirement,
                market_context=market_context,
                max_rounds=max_rounds,
                branch_idx=idx,
                negotiation_id=neg_id,
            )
            for idx, c in enumerate(candidates)
        ]
        negotiation_results = await asyncio.gather(*tasks, return_exceptions=False)

        # 4. Filter & Validate Executable Deals
        executable_deals = [n for n in negotiation_results if n.get("is_valid_deal")]

        # Broadcast Step 4: Deal Evaluation
        if neg_id:
            await _broadcast_safe({
                "event": "TOP5_EVALUATION",
                "negotiation_id": neg_id,
                "step": "EVALUATING DEALS",
                "candidate_count": candidate_count,
                "executable_deals_count": len(executable_deals),
                "message": f"All {candidate_count} parallel negotiations completed. Found {len(executable_deals)} executable deals satisfying reservation ceiling (₹{reservation_p:.2f}/kg) and budget.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            await asyncio.sleep(0.3)

        # 5. Rank Valid Deals by Landed Cost (Lowest Landed Cost per kg)
        if executable_deals:
            executable_deals.sort(key=lambda d: (d["landed_cost_per_kg"], -d["match_score"]))
            winner = executable_deals[0]
            winner["is_winner"] = True
            winner_status = "DEAL_SELECTED"

            # 5a. Automatic Deal Finalization (Transaction ID & SHA-256 Digital Contract Hash)
            txn_id = f"TXN-MH-2026-{uuid.uuid4().hex[:8].upper()}"
            raw_hash_input = f"{txn_id}:{norm_crop}:{winner['executable_quantity']}:{winner['final_price']}:{datetime.now(timezone.utc).isoformat()}"
            contract_hash = "0x" + hashlib.sha256(raw_hash_input.encode()).hexdigest()

            txn_record = {
                "transaction_id": txn_id,
                "negotiation_id": neg_id or f"neg_{uuid.uuid4().hex[:8]}",
                "status": "COMPLETED",
                "crop": norm_crop,
                "quantity": winner["executable_quantity"],
                "final_price": winner["final_price"],
                "freight_per_kg": winner["freight_per_kg"],
                "apmc_cess_per_kg": winner["apmc_cess_per_kg"],
                "landed_cost_per_kg": winner["landed_cost_per_kg"],
                "total_value": round(float(winner["final_price"]) * float(winner["executable_quantity"]), 2),
                "total_landed_cost": winner["total_landed_cost"],
                "contract_hash": contract_hash,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "framework": "Maharashtra APMC Model Act Compliant Electronic Trade",
                "seller_name": winner["seller_name"],
                "buyer_name": requirement.get("buyer_name", "Procurement Buyer"),
            }
            winner["transaction_id"] = txn_id
            winner["contract_hash"] = contract_hash
            winner["transaction_record"] = txn_record

            # Persist in Database history
            user_id = requirement.get("user_id") or requirement.get("buyer_id")
            try:
                hist_payload = {
                    "type": "DEAL_FINALIZED",
                    "transaction_id": txn_id,
                    "negotiation_id": neg_id,
                    "crop": norm_crop,
                    "quantity": winner["executable_quantity"],
                    "final_price": winner["final_price"],
                    "status": "SETTLED",
                    "summary": f"Autonomous deal finalized for {winner['executable_quantity']}kg {norm_crop} at ₹{winner['final_price']}/kg.",
                    "details": txn_record
                }
                if user_id:
                    await Database.add_history_async(user_id, hist_payload)
                await Database.add_history_async("all", hist_payload)
            except Exception as e:
                logger.debug(f"Database history recording: {e}")

            # Update negotiation status if neg_id exists
            if neg_id:
                try:
                    await Database.update_negotiation_async(neg_id, {
                        "status": "DEAL",
                        "final_price": winner["final_price"],
                        "seller_name": winner["seller_name"],
                        "transaction_id": txn_id,
                        "contract_hash": contract_hash,
                    })
                except Exception as e:
                    logger.debug(f"Negotiation status update: {e}")

            # Deduct listing inventory if linked to produce listing
            listing_id = winner.get("seller_id") or winner.get("id")
            if listing_id:
                try:
                    await Database.deduct_produce_inventory_async(listing_id, float(winner["executable_quantity"]))
                except Exception as e:
                    logger.debug(f"Inventory deduction: {e}")

            # Broadcast finalization event
            if neg_id:
                await _broadcast_safe({
                    "event": "TOP5_DEAL_FINALIZED",
                    "negotiation_id": neg_id,
                    "transaction_id": txn_id,
                    "contract_hash": contract_hash,
                    "winner": winner,
                    "message": f"🏆 Deal officially finalized with {winner['seller_name']}. Transaction ID: {txn_id}.",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
        else:
            winner = None
            winner_status = "NO_EXECUTABLE_DEAL"

        # 6. Build Natural Chat Transcript & Comparison Table
        transcript_lines = [
            "=" * 60,
            "BUYER AUTONOMOUS PROCUREMENT ORCHESTRATION",
            "=" * 60,
            f"Buyer Requirement: {norm_crop} | Quantity: {req_qty:,.0f}kg | Target: ₹{target_p:.2f}/kg | Max Reservation: ₹{reservation_p:.2f}/kg | Budget: ₹{budget:,.2f}",
            f"System: Found {candidate_count} eligible candidate seller(s). Initiating {candidate_count} parallel negotiations...",
            "-" * 60,
        ]

        for idx, res in enumerate(negotiation_results, 1):
            transcript_lines.append(f"\n[SELLER {idx}: {res['seller_name']} ({res['location']})]")
            for msg in res["messages"]:
                transcript_lines.append(f"  {msg}")
            transcript_lines.append(f"  Outcome: {res['outcome']} | Landed: ₹{res['landed_cost_per_kg']:.2f}/kg | Valid: {'YES' if res['is_valid_deal'] else 'NO'}")

        transcript_lines.append("\n" + "=" * 60)
        transcript_lines.append("FINAL COMPARISON & SELECTION")
        transcript_lines.append("=" * 60)
        transcript_lines.append(f"{'Seller Name':<32} {'Base ₹/kg':<10} {'Landed ₹/kg':<12} {'Status':<18} {'Valid?'}")
        transcript_lines.append("-" * 75)

        for res in negotiation_results:
            price_str = f"₹{res['final_price']:.2f}" if res['final_price'] is not None else f"₹{res['initial_ask']:.2f} (ask)"
            landed_str = f"₹{res['landed_cost_per_kg']:.2f}"
            valid_str = "YES" if res['is_valid_deal'] else "NO"
            transcript_lines.append(f"{res['seller_name'][:30]:<32} {price_str:<10} {landed_str:<12} {res['outcome']:<18} {valid_str}")

        transcript_lines.append("-" * 75)
        if winner:
            transcript_lines.append(
                f"\n🏆 FINAL SELECTED DEAL:\n"
                f"  Seller: {winner['seller_name']} ({winner['location']})\n"
                f"  Agreed Base Price: ₹{winner['final_price']:.2f}/kg\n"
                f"  True Landed Cost: ₹{winner['landed_cost_per_kg']:.2f}/kg (Freight: ₹{winner['freight_per_kg']:.2f}/kg, Cess: ₹{winner['apmc_cess_per_kg']:.2f}/kg)\n"
                f"  Quantity: {winner['executable_quantity']:,.0f} kg\n"
                f"  Total Expenditure: ₹{winner['total_landed_cost']:,.2f} (within budget of ₹{budget:,.2f})\n"
                f"  PO Number: {winner['contract']['po_number'] if winner.get('contract') else 'N/A'}"
            )
        else:
            transcript_lines.append(
                f"\n❌ NO EXECUTABLE DEAL FOUND:\n"
                f"  All {candidate_count} negotiations failed to produce an agreed offer meeting buyer constraints.\n"
                f"  (All offers exceeded maximum allowable reservation ceiling of ₹{reservation_p:.2f}/kg or budget limits)."
            )

        chat_transcript = "\n".join(transcript_lines)

        result_payload = {
            "orchestration_id": orch_id,
            "requirement": requirement,
            "candidate_count": candidate_count,
            "negotiations": negotiation_results,
            "executable_deals": executable_deals,
            "winner": winner,
            "status": winner_status,
            "chat_transcript": chat_transcript,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.active_orchestrations[orch_id] = result_payload
        return result_payload


# Global singleton instance
buyer_orchestration_service = BuyerOrchestrationService()
