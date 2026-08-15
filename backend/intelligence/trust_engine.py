"""
backend/intelligence/trust_engine.py

Deterministic trust calculation engine for AgriNegotiator.
Manages user reputation, penalties, and risk modifiers.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger("TrustEngine")

class TrustEngine:
    """Manages trust scores and reputation decay."""
    
    def calculate_new_score(self, current_score: float, event_type: str, is_buyer: bool = False) -> float:
        """Calculate the new trust score based on the event."""
        delta = 0.0
        
        if event_type == "DEAL_COMPLETED":
            delta = +0.2
        elif event_type == "DEAL_REJECTED_LATE":
            delta = -0.5
        elif event_type == "DELIVERY_DEFAULT":
            delta = -2.0
        elif event_type == "PAYMENT_DEFAULT" and is_buyer:
            delta = -2.5
        elif event_type == "UNREASONABLE_NEGOTIATION":
            delta = -0.1
            
        new_score = current_score + delta
        # Clamp between 0 and 5
        new_score = max(0.0, min(5.0, new_score))
        
        logger.info(f"Trust updated: {current_score} -> {new_score} (Event: {event_type})")
        return round(new_score, 2)
        
    def get_risk_modifier(self, trust_score: float) -> str:
        """Return a string modifier for the LLM prompt based on trust."""
        if trust_score >= 4.5:
            return "Highly trusted. Excellent reputation. Safe for upfront payment."
        elif trust_score >= 3.5:
            return "Average trust. Normal terms apply."
        elif trust_score >= 2.0:
            return "Low trust. Demand payment on delivery or Escrow."
        else:
            return "CRITICAL RISK. History of defaults. Proceed with extreme caution."


trust_engine = TrustEngine()

