import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from intelligence.llm_client import LLMClient


class AgentReasoning:
    """
    AgentReasoning acts as a bridge between agents
    and the LLM reasoning engine.
    """

    def __init__(self):

        self.llm = LLMClient()

    # ----------------------------------------
    # Farmer decision reasoning
    # ----------------------------------------

    def farmer_decision(
        self,
        offered_price,
        target_price,
        market_price,
        quantity
    ):

        result = self.llm.negotiation_reasoning(
            role="Farmer",
            offered_price=offered_price,
            target_price=target_price,
            market_price=market_price,
            quantity=quantity
        )

        return self._parse_decision(result)

    # ----------------------------------------
    # Buyer decision reasoning
    # ----------------------------------------

    def buyer_decision(
        self,
        offered_price,
        target_price,
        market_price,
        quantity
    ):

        result = self.llm.negotiation_reasoning(
            role="Buyer",
            offered_price=offered_price,
            target_price=target_price,
            market_price=market_price,
            quantity=quantity
        )

        return self._parse_decision(result)

    # ----------------------------------------
    # Negotiation strategy analysis
    # ----------------------------------------

    def analyze_negotiation(self, negotiation_history):

        return self.llm.analyze_strategy(negotiation_history)

    # ----------------------------------------
    # Market reasoning
    # ----------------------------------------

    def market_insight(
        self,
        demand_level,
        supply_level,
        market_price
    ):

        return self.llm.market_analysis(
            demand_level,
            supply_level,
            market_price
        )

    # ----------------------------------------
    # Parse LLM decision safely
    # ----------------------------------------

    def _parse_decision(self, result):

        if result is None:

            return {
                "decision": "COUNTER",
                "counter_price": None,
                "reason": "LLM unavailable fallback"
            }

        decision = result.get("decision", "COUNTER")

        counter_price = result.get("counter_price")

        reason = result.get("reason", "No reasoning provided")

        return {
            "decision": decision,
            "counter_price": counter_price,
            "reason": reason
        }


# ----------------------------------------
# Test
# ----------------------------------------

if __name__ == "__main__":

    reasoning = AgentReasoning()

    decision = reasoning.farmer_decision(
        offered_price=18,
        target_price=22,
        market_price=20,
        quantity=500
    )

    print("\nAgent Decision\n")
    print(decision)