"""
backend/intelligence/learning_engine.py

Reflection-Based Reinforcement Learning (R-RL) engine for AgriNegotiator.
Calculates rewards mathematically and triggers Reflection Agent for insight generation.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger("LearningEngine")

class LearningEngine:
    """Manages reward calculations and triggers post-deal learning."""
    
    def calculate_rewards(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Calculate the deterministic rewards for Farmer and Buyer based on the deal outcome."""
        
        status = state.get("status")
        min_price = state.get("min_price", 1.0)
        market_price = state.get("market_price", 1.0)
        deal_price = state.get("latest_buyer_offer", 0)
        buyer_budget = state.get("buyer_profile", {}).get("budget", 100000)
        quantity = state.get("quantity", 1.0)
        
        rewards = {
            "farmer_reward": 0.0,
            "buyer_reward": 0.0,
            "platform_fairness": 0.0,
            "batna_violation": 0.0
        }
        
        if status == "DEAL":
            # Farmer Reward: (deal_price - min_price) / min_price
            rewards["farmer_reward"] = round((deal_price - min_price) / max(min_price, 0.1) * 10, 2)
            
            # Buyer Reward: (budget_ceiling - deal_price)
            budget_ceiling_per_kg = buyer_budget / quantity
            rewards["buyer_reward"] = round((budget_ceiling_per_kg - deal_price) / max(deal_price, 0.1) * 10, 2)
            
            # Platform Fairness: High reward if deal is within 5% of market price
            if abs(deal_price - market_price) / market_price <= 0.05:
                rewards["platform_fairness"] = 10.0
        
        elif status == "REJECT":
            rewards["farmer_reward"] = -5.0
            rewards["buyer_reward"] = -5.0
            
            # BATNA Violation: If farmer rejected but processor fallback was worse
            processor_salvage = market_price * 0.8
            if deal_price > processor_salvage:
                rewards["batna_violation"] = -10.0
                
        logger.info(f"Calculated Rewards: {rewards}")
        return rewards


learning_engine = LearningEngine()

