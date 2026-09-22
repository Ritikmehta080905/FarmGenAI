"""
backend/agents/stakeholders/farmer_agent.py

Farmer Stakeholder Agent implementation.
Extends BaseAgent. Replaces the legacy `agents/farmer_agent.py`.
Enforces strict business rules via FarmerBusinessRules.
"""

from typing import Dict, Any, Tuple
import json
from backend.agents.common.core import BaseAgent, AgentValidator
from backend.core.business_rules import FarmerBusinessRules, StorageRequirementEvaluator
from backend.agents.prompts import FARMER_PROMPT

class FarmerValidator(AgentValidator):
    def validate(self, output: Dict[str, Any], state: Any) -> Tuple[bool, str, Dict[str, Any]]:
        decision = output.get("decision", "COUNTER").upper()
        price = float(output.get("counter_price", state.get("latest_buyer_offer", state.get("min_price", 0.0))))
        message = output.get("reason", "")
        
        # Hard Rule 1: Min Price Floor
        if decision == "ACCEPT":
            is_valid, reason, action = FarmerBusinessRules.validate_offer(
                offer_price=state.get("latest_buyer_offer", state.get("min_price", 0.0)),
                farmer_min_price=state["min_price"],
                crop=state["crop"]
            )
            if not is_valid:
                return False, reason, {
                    "decision": action,
                    "counter_price": state["min_price"],
                    "reason": f"LLM Override: {reason}"
                }
                
        # Hard Rule 2: Counter Price Math
        if decision == "COUNTER":
            if price < state["min_price"]:
                return False, "Counter price below minimum", {
                    "decision": "COUNTER",
                    "counter_price": state["min_price"],
                    "reason": "Adjusted to minimum price floor."
                }
                
        return True, "", output


class FarmerAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="farmer_01", stakeholder_type="FARMER")
        self.validator = FarmerValidator()

    async def build_prompt(self, state: Any) -> str:
        # Evaluate storage urgency instead of hardcoded `if shelf_life <= 5:`
        storage_urgency = StorageRequirementEvaluator.evaluate(state["spoilage_days"])
        
        return FARMER_PROMPT.format(
            crop=state["crop"],
            quantity=state["quantity"],
            min_price=state["min_price"],
            target_price=state.get("target_price", state["min_price"] * 1.2),
            location=state["location"],
            shelf_life=state["spoilage_days"],
            storage_urgency=storage_urgency,
            market_price=state.get("market_price", 0.0),
            buyer_offer=state.get("latest_buyer_offer", 0.0),
            history=state.get("history", []),
            market_intelligence=state.get("market_intelligence", ""),
            rag_context=state.get("rag_context", "")
        )

    async def process_response(self, response_text: str, state: Any) -> Dict[str, Any]:
        from backend.agents.graph_orchestrator import _parse_json_response
        
        # 1. Parse Output
        parsed = await _parse_json_response(response_text)
        if not parsed:
            parsed = {"decision": "COUNTER", "counter_price": state["min_price"], "reason": "Failsafe fallback"}

        # 2. Validate against Business Rules
        is_valid, error_msg, corrected = self.validator.validate(parsed, state)
        if not is_valid:
            parsed = corrected

        decision = parsed.get("decision", "COUNTER")
        counter_price = parsed.get("counter_price", state.get("latest_buyer_offer", state.get("min_price", 0.0)))
        reason = parsed.get("reason", "")
        
        current_round = state.get("round", 0)
        logs = [f"👨‍🌾 [Farmer] {decision} ₹{counter_price}/kg: {reason}"]
        history = list(state.get("history", []))
        
        record = {
            "round": current_round,
            "agent": "Farmer",
            "price": counter_price if decision == "COUNTER" else state.get("latest_buyer_offer", state.get("min_price", 0.0)),
            "decision": decision,
            "quantity": state["quantity"],
            "message": reason,
            "reason": reason
        }
        history.append(record)

        if decision == "ACCEPT":
            return {
                "status": "DEAL",
                "history": history,
                "latest_farmer_ask": state.get("latest_buyer_offer", state.get("min_price", 0.0)),
                "logs": logs
            }
        elif decision == "REJECT":
            return {
                "status": "REJECT",
                "history": history,
                "logs": logs
            }
        else:
            return {
                "history": history,
                "latest_farmer_ask": counter_price,
                "logs": logs
            }
