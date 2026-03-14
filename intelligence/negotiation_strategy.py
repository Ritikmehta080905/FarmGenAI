import random
from intelligence.agent_reasoning import AgentReasoning


class NegotiationStrategy:
    """
    Defines different negotiation behaviors for agents.

    Strategies influence how agents react to offers.
    """

    def __init__(self, strategy_type="balanced"):

        self.strategy_type = strategy_type
        self.reasoning = AgentReasoning()

    # ----------------------------------------
    # Main decision interface
    # ----------------------------------------

    def decide(
        self,
        role,
        offered_price,
        target_price,
        market_price,
        quantity
    ):

        # Modify parameters depending on strategy
        adjusted_target = self._adjust_target_price(
            target_price,
            market_price
        )

        if role == "Farmer":

            decision = self.reasoning.farmer_decision(
                offered_price,
                adjusted_target,
                market_price,
                quantity
            )

        else:

            decision = self.reasoning.buyer_decision(
                offered_price,
                adjusted_target,
                market_price,
                quantity
            )

        return decision

    # ----------------------------------------
    # Adjust target price based on strategy
    # ----------------------------------------

    def _adjust_target_price(self, target_price, market_price):

        if self.strategy_type == "aggressive":

            # push price higher
            return target_price * 1.1

        elif self.strategy_type == "cooperative":

            # easier to close deals
            return (target_price + market_price) / 2

        elif self.strategy_type == "profit_max":

            # aim for maximum margin
            return target_price * 1.2

        else:
            # balanced
            return target_price

    # ----------------------------------------
    # Generate random strategy (for simulation)
    # ----------------------------------------

    @staticmethod
    def random_strategy():

        strategies = [
            "aggressive",
            "balanced",
            "cooperative",
            "profit_max"
        ]

        return random.choice(strategies)

    # ----------------------------------------
    # Strategy description
    # ----------------------------------------

    def describe(self):

        descriptions = {

            "aggressive":
                "Agent pushes for higher prices and rarely accepts early.",

            "balanced":
                "Agent negotiates moderately and aims for fair deals.",

            "cooperative":
                "Agent prioritizes closing deals quickly.",

            "profit_max":
                "Agent focuses on maximizing profit margins."
        }

        return descriptions.get(
            self.strategy_type,
            "Balanced negotiation strategy."
        )


# ----------------------------------------
# Test
# ----------------------------------------

if __name__ == "__main__":

    strategy = NegotiationStrategy("aggressive")

    decision = strategy.decide(
        role="Farmer",
        offered_price=18,
        target_price=22,
        market_price=20,
        quantity=500
    )

    print("\nStrategy:", strategy.strategy_type)
    print(strategy.describe())

    print("\nDecision:")
    print(decision)