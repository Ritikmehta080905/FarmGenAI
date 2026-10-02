"""
backend/services/buyer_workflow_service.py

Buyer Agent — Phase 1: Intelligent Agent Orchestration Layer
------------------------------------------------------------
Implements:
1. Buyer Workflow Memory (Authoritative business state + conversation context).
2. Requirement-scoped & Buyer-scoped isolation.
3. Authoritative Farmer Deal Gate (No valid deal = No downstream execution).
4. Valid-Next-Agent Intelligence ("Why this agent?", "Why not this agent?").
5. Deterministic Buyer Policy (Clean interface for future RL insertion).
6. Controlled Handoff to existing Transport Agent.
7. Warehouse routing/link placeholder only (NEVER marked complete).
8. Durable persistence across request boundaries and browser reload.
"""

import uuid
import logging
from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from database.db import Database
from backend.agents.transport_agent.graph import run_transport_workflow

logger = logging.getLogger("BuyerWorkflowService")

# Canonical Agent Identifiers
AGENT_FARMER = "FARMER"
AGENT_TRANSPORT = "TRANSPORT"
AGENT_WAREHOUSE = "WAREHOUSE"
SUPPORTED_AGENTS = {AGENT_FARMER, AGENT_TRANSPORT, AGENT_WAREHOUSE}

# Authoritative Deal Statuses
DEAL_STATUS_SUCCESS = "SUCCESS"
DEAL_STATUS_FAILED = "FAILED"
DEAL_STATUS_TIMEOUT = "TIMEOUT"
DEAL_STATUS_WITHDRAWN = "WITHDRAWN"
DEAL_STATUS_EXPIRED = "EXPIRED"
DEAL_STATUS_PENDING = "PENDING"


# ─────────────────────────────────────────────────────────────────────────────
# 1. POLICY INTERFACE (Deterministic now, RL-Ready for Phase 4)
# ─────────────────────────────────────────────────────────────────────────────

class BuyerPolicy(ABC):
    """
    Abstract interface for Buyer orchestration action selection.
    In Phase 1, DeterministicBuyerPolicy implements rule-based selection.
    In Phase 4/5, RLBuyerPolicy will implement learned policy selection
    using the exact same contract without changing orchestration mechanics.
    """
    @abstractmethod
    def select_action(
        self,
        state: Dict[str, Any],
        valid_actions: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Given workflow state and valid actions, select the next action to execute."""
        pass


class DeterministicBuyerPolicy(BuyerPolicy):
    """
    Phase 1 Deterministic Policy.
    Picks the next valid action based on strict supply-chain dependencies:
    1. If workflow is ready to complete -> COMPLETE
    2. If farmer deal failed -> STOP
    3. If TRANSPORT is eligible -> TRANSPORT
    4. If WAREHOUSE route is ready -> WAREHOUSE
    5. If farmer negotiation active -> WAIT_FARMER
    """
    def select_action(
        self,
        state: Dict[str, Any],
        valid_actions: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        if not valid_actions:
            return None

        action_map = {a["action"]: a for a in valid_actions}

        # Deterministic priority hierarchy
        if "COMPLETE" in action_map:
            return action_map["COMPLETE"]
        if "STOP" in action_map:
            return action_map["STOP"]
        if "TRANSPORT" in action_map:
            return action_map["TRANSPORT"]
        if "WAREHOUSE" in action_map:
            return action_map["WAREHOUSE"]
        if "WAIT_FARMER" in action_map:
            return action_map["WAIT_FARMER"]
        if "FARMER_RETRY" in action_map:
            return action_map["FARMER_RETRY"]

        return valid_actions[0]


# ─────────────────────────────────────────────────────────────────────────────
# 2. BUYER WORKFLOW ORCHESTRATION SERVICE
# ─────────────────────────────────────────────────────────────────────────────

class BuyerWorkflowService:
    def __init__(self, policy: Optional[BuyerPolicy] = None):
        self.policy: BuyerPolicy = policy or DeterministicBuyerPolicy()

    # ── State Creation & Initialization ─────────────────────────────────────
    async def initialize_workflow(
        self,
        requirement_id: str,
        buyer_id: str,
        crop: str,
        quantity: float,
        quality: str = "Grade A",
        pickup_location: str = "Maharashtra",
        delivery_location: str = "Pune, Maharashtra",
        delivery_deadline_hours: float = 24.0,
        selected_services: Optional[Dict[str, Any]] = None,
        selected_agents: Optional[List[str]] = None,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates or restores requirement-scoped Buyer Workflow Memory.
        Maps requested frontend services into the requested agent scope.
        """
        wf_id = workflow_id or f"wf_{str(uuid.uuid4())[:8]}"

        # Deduce selected agents from explicit list or services dict
        agents = []
        if selected_agents is not None:
            agents = [a.upper() for a in selected_agents if a.upper() in SUPPORTED_AGENTS]
        elif selected_services:
            # Always include Farmer if farmer_matching or negotiation requested
            if selected_services.get("farmer_matching") or selected_services.get("negotiation") or selected_services.get("market_intelligence"):
                agents.append(AGENT_FARMER)
            if selected_services.get("transport"):
                agents.append(AGENT_TRANSPORT)
            if selected_services.get("warehouse"):
                agents.append(AGENT_WAREHOUSE)

        if AGENT_FARMER not in agents:
            # Baseline: Farmer is always the entry prerequisite for procurement
            agents.insert(0, AGENT_FARMER)

        now_iso = datetime.now(timezone.utc).isoformat()
        initial_pending = [a for a in agents if a != AGENT_FARMER]

        state: Dict[str, Any] = {
            "workflow_id": wf_id,
            "requirement_id": requirement_id,
            "buyer_id": buyer_id,
            "crop": crop,
            "quantity": float(quantity),
            "quality": quality,
            "pickup_location": pickup_location,
            "delivery_location": delivery_location,
            "delivery_deadline_hours": float(delivery_deadline_hours),

            # Requested scope
            "selected_agents": agents,
            "current_agent": AGENT_FARMER,
            "completed_agents": [],
            "failed_agents": [],
            "pending_agents": initial_pending,

            # Authoritative Farmer Deal State
            "farmer_deal": {
                "status": None,
                "deal_id": None,
                "transaction_id": None,
                "supplier_id": None,
                "supplier_name": None,
                "supplier_location": pickup_location,
                "quantity": None,
                "price": None,
                "contract_hash": None,
                "finalized_at": None,
                "valid": False,
                "expiry_time": None
            },

            # Outcomes from downstream agents
            "agent_outcomes": {},

            # Two separate memory streams
            "conversation_context": [
                {
                    "timestamp": now_iso,
                    "agent": "BUYER_ORCHESTRATOR",
                    "event": "WORKFLOW_INITIALIZED",
                    "message": f"Initialized requirement workflow for {quantity}kg {crop}. Selected agents: {agents}."
                }
            ],
            "audit_logs": [
                {
                    "timestamp": now_iso,
                    "event": "STATE_INITIALIZED",
                    "reason": f"Buyer selected scope: {agents}. Farmer deal required as gate.",
                    "valid_next_actions": ["FARMER"]
                }
            ],

            "last_action": "INITIALIZE",
            "last_response": None,
            "workflow_status": "FARMER_NEGOTIATING",
            "created_at": now_iso,
            "updated_at": now_iso
        }

        # Persist to durable database
        persisted = await Database.upsert_buyer_workflow_async(state)
        logger.info(f"Initialized Buyer Workflow: {wf_id} for req: {requirement_id}")
        return persisted

    # ── State Retrieval ──────────────────────────────────────────────────────
    async def get_workflow_state(
        self,
        workflow_id: Optional[str] = None,
        requirement_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieves workflow memory by workflow_id or requirement_id."""
        return await Database.get_buyer_workflow_async(
            workflow_id=workflow_id,
            requirement_id=requirement_id
        )

    # ── Authoritative Farmer Deal Verification ───────────────────────────────
    async def verify_farmer_deal_authoritative(
        self,
        deal_id: Optional[str] = None,
        negotiation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pillar 7 Rule: DO NOT TRUST FRONTEND OR LLM FOR DEAL STATE.
        Queries the authoritative backend database to verify that the negotiation
        actually has a status of DEAL or COMPLETED and is not expired or withdrawn.
        """
        target_id = deal_id or negotiation_id
        if not target_id:
            return {"valid": False, "status": DEAL_STATUS_FAILED, "reason": "No deal identifier provided."}

        # Check in negotiations table
        neg = await Database.get_negotiation_async(target_id)
        if not neg:
            # Fallback check by stripping prefixes or searching list
            negs = await Database.list_negotiations_async(limit=100)
            neg = next((n for n in negs if n.get("negotiation_id") == target_id or n.get("id") == target_id), None)

        if not neg:
            return {"valid": False, "status": DEAL_STATUS_FAILED, "reason": f"Deal {target_id} not found in authoritative database."}

        neg_status = str(neg.get("status", "")).upper()

        if neg_status in ("DEAL", "COMPLETED"):
            # Check price and quantity sanity
            final_p = float(neg.get("final_price") or neg.get("price") or 0.0)
            final_q = float(neg.get("quantity") or 0.0)
            if final_p <= 0 or final_q <= 0:
                return {
                    "valid": False,
                    "status": DEAL_STATUS_FAILED,
                    "reason": f"Deal {target_id} has invalid non-positive terms (price={final_p}, qty={final_q})."
                }

            supplier_loc = neg.get("location") or neg.get("pickup_location")
            if not supplier_loc and neg.get("listing_id"):
                try:
                    listing = await Database.get_produce_listing_async(neg["listing_id"])
                    if listing:
                        supplier_loc = listing.get("location")
                except Exception:
                    pass

            return {
                "valid": True,
                "status": DEAL_STATUS_SUCCESS,
                "deal_id": target_id,
                "transaction_id": neg.get("transaction_id") or f"TXN-MH-2026-{str(target_id).replace('neg_', '').upper()}",
                "supplier_id": neg.get("farmer_id") or "farmer_verified",
                "supplier_name": neg.get("farmer_name") or neg.get("farmer") or "Verified APMC Farmer",
                "supplier_location": supplier_loc,
                "crop": neg.get("crop"),
                "quantity": final_q,
                "price": final_p,
                "contract_hash": neg.get("contract_hash"),
                "finalized_at": datetime.now(timezone.utc).isoformat()
            }
        elif neg_status in ("WITHDRAWN", "CANCELLED"):
            return {"valid": False, "status": DEAL_STATUS_WITHDRAWN, "reason": f"Deal {target_id} was withdrawn/cancelled."}
        elif neg_status in ("EXPIRED", "TIMEOUT"):
            return {"valid": False, "status": DEAL_STATUS_EXPIRED, "reason": f"Deal {target_id} expired."}
        else:
            return {"valid": False, "status": DEAL_STATUS_FAILED, "reason": f"Deal {target_id} has non-deal status: {neg_status}."}

    # ── Deal Finalization / State Update Hook ────────────────────────────────
    async def record_farmer_deal_outcome(
        self,
        requirement_id: str,
        deal_id: str,
        outcome_status: str,  # "SUCCESS", "FAILED", "WITHDRAWN", "EXPIRED"
        deal_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Updates Buyer Workflow Memory when Farmer negotiation concludes.
        Re-evaluates authoritative deal validity before updating downstream eligibility.
        """
        state = await self.get_workflow_state(requirement_id=requirement_id)
        if not state:
            raise ValueError(f"Workflow state not found for requirement: {requirement_id}")

        now_iso = datetime.now(timezone.utc).isoformat()
        current_completed = list(state.get("completed_agents", []))
        current_failed = list(state.get("failed_agents", []))
        audit = list(state.get("audit_logs", []))
        conv = list(state.get("conversation_context", []))

        auth_verification = {"valid": False}
        if outcome_status == DEAL_STATUS_SUCCESS:
            # Verify deal authoritatively against backend DB
            auth_verification = await self.verify_farmer_deal_authoritative(deal_id)
            if not auth_verification["valid"]:
                logger.warning(f"Authoritative verification failed for deal {deal_id}: {auth_verification.get('reason')}")
                outcome_status = auth_verification.get("status", DEAL_STATUS_FAILED)

        if outcome_status == DEAL_STATUS_SUCCESS:
            auth_deal = auth_verification
            state["farmer_deal"] = {
                "status": DEAL_STATUS_SUCCESS,
                "deal_id": deal_id,
                "transaction_id": auth_deal.get("transaction_id"),
                "supplier_id": auth_deal.get("supplier_id"),
                "supplier_name": auth_deal.get("supplier_name"),
                "supplier_location": (
                    auth_deal.get("supplier_location")
                    or (deal_details.get("supplier_location") if deal_details else None)
                    or state.get("pickup_location")
                    or "Nashik APMC, Maharashtra"
                ),
                "crop": auth_deal.get("crop", state.get("crop")),
                "quantity": auth_deal.get("quantity", state.get("quantity")),
                "price": auth_deal.get("price"),
                "contract_hash": auth_deal.get("contract_hash"),
                "finalized_at": auth_deal.get("finalized_at", now_iso),
                "valid": True
            }
            if AGENT_FARMER not in current_completed:
                current_completed.append(AGENT_FARMER)
            if AGENT_FARMER in current_failed:
                current_failed.remove(AGENT_FARMER)

            state["workflow_status"] = "FARMER_DEAL_SUCCESS"
            conv.append({
                "timestamp": now_iso,
                "agent": AGENT_FARMER,
                "event": "DEAL_SUCCESS",
                "message": f"Farmer deal confirmed: {state['farmer_deal']['quantity']}kg {state['farmer_deal']['crop']} at ₹{state['farmer_deal']['price']}/kg (Deal ID: {deal_id})."
            })
            audit.append({
                "timestamp": now_iso,
                "event": "FARMER_DEAL_VERIFIED",
                "reason": f"Authoritative backend verified deal {deal_id}. Downstream routing is now eligible.",
                "deal_id": deal_id
            })
        else:
            # Farmer Deal Failed, Withdrawn, or Expired
            state["farmer_deal"] = {
                "status": outcome_status,
                "deal_id": deal_id,
                "transaction_id": None,
                "supplier_id": None,
                "supplier_name": None,
                "supplier_location": None,
                "quantity": None,
                "price": None,
                "contract_hash": None,
                "finalized_at": now_iso,
                "valid": False
            }
            if AGENT_FARMER not in current_failed:
                current_failed.append(AGENT_FARMER)
            if AGENT_FARMER in current_completed:
                current_completed.remove(AGENT_FARMER)

            state["workflow_status"] = f"FARMER_DEAL_{outcome_status}"
            conv.append({
                "timestamp": now_iso,
                "agent": AGENT_FARMER,
                "event": f"DEAL_{outcome_status}",
                "message": f"Farmer negotiation concluded with status: {outcome_status}. Downstream agents blocked."
            })
            audit.append({
                "timestamp": now_iso,
                "event": "FARMER_DEAL_INVALID",
                "reason": f"Farmer deal status is {outcome_status}. CRITICAL INVARIANT: No valid deal means no downstream supply-chain agent can execute.",
                "deal_id": deal_id
            })

        state["completed_agents"] = current_completed
        state["failed_agents"] = current_failed
        state["conversation_context"] = conv
        state["audit_logs"] = audit
        state["updated_at"] = now_iso

        return await Database.upsert_buyer_workflow_async(state)

    # ── Deal Revalidation (Withdrawal & Expiration Checks) ───────────────────
    async def revalidate_deal_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Revalidates existing farmer deal before any downstream handoff.
        If deal was invalidated, marks it invalid and updates memory.
        """
        farmer_deal = state.get("farmer_deal") or {}
        if not farmer_deal.get("valid"):
            return state

        deal_id = farmer_deal.get("deal_id")
        auth = await self.verify_farmer_deal_authoritative(deal_id)
        if not auth["valid"]:
            logger.warning(f"Revalidation of deal {deal_id} failed: {auth.get('reason')}")
            return await self.record_farmer_deal_outcome(
                requirement_id=state["requirement_id"],
                deal_id=deal_id or "invalid_deal",
                outcome_status=auth.get("status", DEAL_STATUS_WITHDRAWN)
            )
        return state

    # ── Valid-Next-Agent Intelligence Service ────────────────────────────────
    def get_valid_next_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Authoritative Decision Engine:
        Answers: 'Given everything that has happened so far, which actions/agents are valid right now?'
        Incorporates 'Why this agent?' and 'Why not this agent?' rationale into every decision.
        """
        valid_actions: List[Dict[str, Any]] = []
        blocked_reasons: Dict[str, str] = {}

        selected_agents = state.get("selected_agents", [])
        completed_agents = set(state.get("completed_agents", []))
        failed_agents = set(state.get("failed_agents", []))
        farmer_deal = state.get("farmer_deal", {})
        deal_valid = bool(farmer_deal.get("valid", False))
        deal_status = farmer_deal.get("status")

        # ── 1. Farmer Gate Evaluation ─────────────────────────────────────────
        if AGENT_FARMER not in completed_agents:
            if deal_status in (DEAL_STATUS_FAILED, DEAL_STATUS_WITHDRAWN, DEAL_STATUS_EXPIRED):
                # Farmer deal failed. Downstream agents are strictly blocked!
                blocked_reasons[AGENT_TRANSPORT] = (
                    f"Why not Transport? Transport was requested, but the required Farmer procurement "
                    f"deal failed (status: {deal_status}). No valid Farmer deal = No downstream execution."
                )
                blocked_reasons[AGENT_WAREHOUSE] = (
                    f"Why not Warehouse? Warehouse was requested, but the required Farmer procurement "
                    f"deal failed (status: {deal_status}). No valid Farmer deal = No downstream execution."
                )

                valid_actions.append({
                    "action": "STOP",
                    "reason": f"Farmer deal failed with status '{deal_status}'. Workflow halted. All downstream agents blocked.",
                    "blocked_reasons": blocked_reasons
                })
                valid_actions.append({
                    "action": "FARMER_RETRY",
                    "reason": "Optionally restart Farmer discovery and negotiation with adjusted parameters.",
                    "blocked_reasons": blocked_reasons
                })
                return valid_actions

            # Negotiation still in progress
            blocked_reasons[AGENT_TRANSPORT] = "Why not Transport? Waiting for Farmer negotiation to reach an authoritative deal."
            blocked_reasons[AGENT_WAREHOUSE] = "Why not Warehouse? Waiting for Farmer negotiation to reach an authoritative deal."
            valid_actions.append({
                "action": "WAIT_FARMER",
                "reason": "Farmer negotiation is currently active and awaiting authoritative counter-offers or deal settlement.",
                "blocked_reasons": blocked_reasons
            })
            return valid_actions

        # ── 2. Downstream Agent Intelligence (Only when Farmer Deal is Valid) ─
        if not deal_valid:
            # Stale or invalidated deal
            blocked_reasons[AGENT_TRANSPORT] = "Why not Transport? Farmer deal is marked invalid."
            blocked_reasons[AGENT_WAREHOUSE] = "Why not Warehouse? Farmer deal is marked invalid."
            valid_actions.append({
                "action": "STOP",
                "reason": "Farmer deal is invalid or has expired. Downstream agents are strictly blocked.",
                "blocked_reasons": blocked_reasons
            })
            return valid_actions

        # Check Unselected Invariant
        for agent in [AGENT_TRANSPORT, AGENT_WAREHOUSE]:
            if agent not in selected_agents:
                blocked_reasons[agent] = f"Why not {agent}? {agent} was not selected in the Buyer requested scope."

        # Check Transport Eligibility
        transport_selected = AGENT_TRANSPORT in selected_agents
        transport_completed = AGENT_TRANSPORT in completed_agents
        transport_failed = AGENT_TRANSPORT in failed_agents

        if transport_selected and not transport_completed and not transport_failed:
            valid_actions.append({
                "action": AGENT_TRANSPORT,
                "eligible_agent": AGENT_TRANSPORT,
                "reason": (
                    "Transport is selected in requested scope, Farmer procurement deal is verified, "
                    "and Transport is the next permitted workflow dependency."
                ),
                "blocked_reasons": {
                    AGENT_WAREHOUSE: "Why not Warehouse yet? Transport was selected and must complete dispatch planning before storage handoff."
                }
            })

        # Check Warehouse Eligibility
        warehouse_selected = AGENT_WAREHOUSE in selected_agents
        warehouse_completed = AGENT_WAREHOUSE in completed_agents

        if warehouse_selected and not warehouse_completed:
            # Dependency: If transport was also selected, transport must finish first
            if transport_selected and not transport_completed:
                blocked_reasons[AGENT_WAREHOUSE] = (
                    "Why not Warehouse yet? Transport is currently pending and must complete before warehouse routing."
                )
            else:
                valid_actions.append({
                    "action": AGENT_WAREHOUSE,
                    "eligible_agent": AGENT_WAREHOUSE,
                    "reason": (
                        "Warehouse is selected in requested scope, Farmer procurement deal is verified "
                        f"{'(and Transport is completed)' if transport_selected else '(Transport not requested)'}. "
                        "Ready for Warehouse routing."
                    ),
                    "blocked_reasons": blocked_reasons
                })

        if not valid_actions:
            valid_actions.append({
                "action": "COMPLETE",
                "reason": "All selected agents in the requested Buyer scope have completed their required stages.",
                "blocked_reasons": blocked_reasons
            })

        return valid_actions

    # ── Action Execution / Handoff ───────────────────────────────────────────
    async def step_workflow(
        self,
        requirement_id: str,
        action_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orchestration Step Execution:
        1. Reads and revalidates state.
        2. Calculates valid next actions.
        3. Uses Policy to select next action.
        4. Dispatches controlled handoff to receiving agent.
        5. Records agent outcome in Buyer memory.
        6. Re-evaluates next actions and persists.
        """
        state = await self.get_workflow_state(requirement_id=requirement_id)
        if not state:
            raise ValueError(f"Workflow not found for requirement: {requirement_id}")

        # Deal revalidation guard
        state = await self.revalidate_deal_state(state)

        valid_actions = self.get_valid_next_actions(state)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Select action via Policy or explicit override
        if action_override:
            selected_action_obj = next((a for a in valid_actions if a["action"] == action_override), None)
            if not selected_action_obj:
                raise ValueError(f"Action '{action_override}' is not valid right now. Valid actions: {[a['action'] for a in valid_actions]}")
        else:
            selected_action_obj = self.policy.select_action(state, valid_actions)

        if not selected_action_obj:
            logger.info(f"No action to execute for workflow {state['workflow_id']}.")
            return state

        action_name = selected_action_obj["action"]
        reason = selected_action_obj.get("reason", "")
        logger.info(f"Executing Buyer Orchestrator Action: {action_name} (Reason: {reason})")

        state["last_action"] = action_name
        state["current_agent"] = selected_action_obj.get("eligible_agent")

        # ── Handoff Branch: TRANSPORT ─────────────────────────────────────────
        if action_name == AGENT_TRANSPORT:
            farmer_deal = state.get("farmer_deal", {})
            qty = float(farmer_deal.get("quantity") or state.get("quantity", 1000.0))
            crop = str(farmer_deal.get("crop") or state.get("crop", "Soybean"))
            pickup = str(farmer_deal.get("supplier_location") or state.get("pickup_location") or "Ahmednagar")
            delivery = str(state.get("delivery_location") or "Pune")
            deal_id = farmer_deal.get("deal_id", "DEAL-UNKN")

            # Controlled Handoff Payload (NO private farmer chat history passed!)
            transport_request = {
                "request_id": f"TR-{state['requirement_id']}-{str(uuid.uuid4())[:4]}",
                "workflow_id": state["workflow_id"],
                "requirement_id": state["requirement_id"],
                "farmer_deal_id": deal_id,
                "crop": crop,
                "quantity_kg": qty,
                "pickup_location": pickup,
                "delivery_location": delivery,
                "delivery_deadline_hours": float(state.get("delivery_deadline_hours") or 24.0),
                "shelf_life_hours": 72.0,
                "refrigerated_required": crop.lower() in {"tomato", "strawberry", "grape", "banana", "mango"}
            }

            state["conversation_context"].append({
                "timestamp": now_iso,
                "agent": "BUYER_ORCHESTRATOR",
                "event": "TRANSPORT_HANDOFF_DISPATCHED",
                "message": f"Handed off {qty}kg {crop} from {pickup} to {delivery} to Transport Agent."
            })

            try:
                # Integrate directly with existing Transport Agent graph
                transport_outcome = await run_transport_workflow(transport_request)
                t_status = transport_outcome.get("status", "UNKNOWN")
                t_plan = transport_outcome.get("final_transport_plan") or {}
                is_successful = bool(t_plan) and t_status not in ("INFEASIBLE", "FAILED", "REJECTED")

                # Store response in Buyer workflow memory
                state["agent_outcomes"][AGENT_TRANSPORT] = {
                    "status": "CONFIRMED" if is_successful else "FAILED",
                    "request_id": transport_request["request_id"],
                    "deal_id": deal_id,
                    "vehicle": t_plan.get("vehicle_name") or transport_outcome.get("selected_vehicle", {}).get("vehicle_type"),
                    "vehicle_type": t_plan.get("vehicle_type"),
                    "route": f"{t_plan.get('pickup_location', pickup)} → {t_plan.get('delivery_location', delivery)}",
                    "distance_km": transport_outcome.get("distance_km"),
                    "cost": t_plan.get("agreed_price") or transport_outcome.get("total_operating_cost"),
                    "response": t_status,
                    "plan": t_plan,
                    "completed_at": now_iso
                }

                if is_successful:
                    if AGENT_TRANSPORT not in state["completed_agents"]:
                        state["completed_agents"].append(AGENT_TRANSPORT)
                    if AGENT_TRANSPORT in state["pending_agents"]:
                        state["pending_agents"].remove(AGENT_TRANSPORT)
                    state["last_response"] = f"Transport confirmed via {state['agent_outcomes'][AGENT_TRANSPORT]['vehicle']} at ₹{state['agent_outcomes'][AGENT_TRANSPORT]['cost']}."
                else:
                    if AGENT_TRANSPORT not in state["failed_agents"]:
                        state["failed_agents"].append(AGENT_TRANSPORT)
                    if AGENT_TRANSPORT in state["pending_agents"]:
                        state["pending_agents"].remove(AGENT_TRANSPORT)
                    state["last_response"] = f"Transport planning failed: {t_status}."

            except Exception as e:
                logger.error(f"Transport execution error: {e}", exc_info=True)
                state["agent_outcomes"][AGENT_TRANSPORT] = {
                    "status": "FAILED",
                    "error": str(e),
                    "completed_at": now_iso
                }
                if AGENT_TRANSPORT not in state["failed_agents"]:
                    state["failed_agents"].append(AGENT_TRANSPORT)
                state["last_response"] = f"Transport error: {e}."

        # ── Handoff Branch: WAREHOUSE ─────────────────────────────────────────
        elif action_name == AGENT_WAREHOUSE:
            # Pillar 30: WAREHOUSE — DO NOT BUILD IT
            # Prepare only route/handoff navigation contract. NEVER mark completed!
            farmer_deal = state.get("farmer_deal", {})
            deal_id = farmer_deal.get("deal_id", "DEAL-UNKN")

            warehouse_handoff = {
                "status": "WAREHOUSE_ROUTE_READY",
                "route": "/dashboard/warehouse",
                "query_params": {
                    "requirement_id": state["requirement_id"],
                    "workflow_id": state["workflow_id"],
                    "farmer_deal_id": deal_id,
                    "crop": state.get("crop"),
                    "quantity": farmer_deal.get("quantity") or state.get("quantity")
                },
                "handoff_ready": True,
                "completed": False,  # Strict: Never mark completed!
                "handed_off_at": now_iso
            }

            state["agent_outcomes"][AGENT_WAREHOUSE] = warehouse_handoff
            state["last_response"] = "Warehouse route is ready. Navigating to warehouse dashboard."
            state["conversation_context"].append({
                "timestamp": now_iso,
                "agent": "BUYER_ORCHESTRATOR",
                "event": "WAREHOUSE_ROUTE_PREPARED",
                "message": f"Warehouse route ready at {warehouse_handoff['route']} for deal {deal_id}."
            })

        # ── Handoff Branch: COMPLETE / STOP ───────────────────────────────────
        elif action_name == "COMPLETE":
            state["workflow_status"] = "COMPLETED"
            state["current_agent"] = None
            state["last_response"] = "Buyer workflow completed all selected stages."
        elif action_name == "STOP":
            state["workflow_status"] = "STOPPED"
            state["current_agent"] = None
            state["last_response"] = "Workflow stopped due to prerequisite failure."

        # Audit Decision Logging
        state["audit_logs"].append({
            "timestamp": now_iso,
            "buyer_id": state["buyer_id"],
            "requirement_id": state["requirement_id"],
            "workflow_id": state["workflow_id"],
            "selected_agents": state["selected_agents"],
            "current_agent": state["current_agent"],
            "farmer_deal_status": state.get("farmer_deal", {}).get("status"),
            "farmer_deal_id": state.get("farmer_deal", {}).get("deal_id"),
            "completed_agents": state["completed_agents"],
            "failed_agents": state["failed_agents"],
            "pending_agents": state["pending_agents"],
            "valid_next_actions": [a["action"] for a in valid_actions],
            "selected_action": action_name,
            "reason": reason
        })

        state["updated_at"] = now_iso
        return await Database.upsert_buyer_workflow_async(state)


# Global singleton instance
buyer_workflow_service = BuyerWorkflowService()
