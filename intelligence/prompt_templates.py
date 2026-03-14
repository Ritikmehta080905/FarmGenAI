class PromptTemplates:
    """
    Contains reusable prompt templates for all LLM interactions
    in the multi-agent negotiation system.
    """

    # ----------------------------------------
    # Negotiation reasoning prompt
    # ----------------------------------------

    @staticmethod
    def negotiation_reasoning_prompt(
        role,
        offered_price,
        target_price,
        market_price,
        quantity
    ):

        return f"""
You are an AI agent participating in an agricultural market negotiation.

Role: {role}

Context:
- Offered price: ₹{offered_price}/kg
- Target price: ₹{target_price}/kg
- Current market price: ₹{market_price}/kg
- Quantity: {quantity} kg

Your goal is to maximize benefit for your role while reaching reasonable agreements.

Decide the next action.

Possible actions:
ACCEPT
COUNTER
REJECT

Rules:
- Accept if offer is fair or profitable
- Counter if negotiation is possible
- Reject if offer is far below expectations

Respond ONLY in JSON format:

{{
 "decision": "ACCEPT | COUNTER | REJECT",
 "counter_price": number or null,
 "reason": "short explanation"
}}
"""

    # ----------------------------------------
    # Negotiation strategy analysis prompt
    # ----------------------------------------

    @staticmethod
    def negotiation_analysis_prompt(negotiation_history):

        return f"""
You are analyzing a negotiation between agents in an agricultural market.

Negotiation history:
{negotiation_history}

Analyze the following:

1. Is the deal fair for both sides?
2. Who currently has stronger bargaining power?
3. What is the best next move for the negotiating agent?

Provide a short explanation.
"""

    # ----------------------------------------
    # Market analysis prompt
    # ----------------------------------------

    @staticmethod
    def market_analysis_prompt(
        demand_level,
        supply_level,
        market_price
    ):

        return f"""
You are an agricultural market analyst.

Market conditions:

Demand level: {demand_level}
Supply level: {supply_level}
Current market price: ₹{market_price}/kg

Explain:

1. Current market situation
2. Expected price trend
3. Suggested pricing strategy for farmers
"""

    # ----------------------------------------
    # Agent explanation prompt
    # ----------------------------------------

    @staticmethod
    def decision_explanation_prompt(decision_data):

        return f"""
Explain the reasoning behind this negotiation decision.

Decision data:
{decision_data}

Provide a short explanation suitable for logs in an AI system.
"""

    # ----------------------------------------
    # Risk evaluation prompt
    # ----------------------------------------

    @staticmethod
    def risk_assessment_prompt(
        shelf_life,
        demand_level,
        market_price
    ):

        return f"""
You are evaluating risk in an agricultural supply chain.

Factors:
Shelf life remaining: {shelf_life} days
Demand level: {demand_level}
Market price: ₹{market_price}/kg

Assess:

1. Risk of spoilage
2. Urgency of selling
3. Recommended negotiation strategy
"""