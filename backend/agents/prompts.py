"""
backend/agents/prompts.py

LangChain prompt templates for the AgriNegotiator multi-agent negotiation graph.
Provides standard structured guidance for each agent node.
"""

from langchain_core.prompts import PromptTemplate

# --- Workflow Planner Prompt ---
PLANNER_PROMPT = PromptTemplate(
    input_variables=["crop", "quantity", "min_price", "location", "shelf_life", "market_price"],
    template="""You are the Workflow Planner for AgriNegotiator.
Analyze the listing:
Crop: {crop}
Quantity: {quantity} kg
Farmer Minimum Price: ₹{min_price}/kg
Location: {location}
Shelf Life: {shelf_life} days
Market Price: ₹{market_price}/kg

Generate a structured negotiation strategy plan. Consider:
1. The perishability of the crop (shelf life).
2. The initial discount threshold or target opening price.
3. Escalation thresholds to storage or processing if direct sales fail.

Output your strategic planning thoughts as a concise, structured plan. Include:
1. Target Buyer Profile (e.g., Premium, Bulk, Mandi)
2. Spoilage risk level (High/Medium/Low)
3. Initial pricing strategy
"""
)

# --- Matching Engine Prompt ---
MATCHING_ENGINE_PROMPT = PromptTemplate(
    input_variables=["crop", "quantity", "min_price", "location", "buyers"],
    template="""You are the Matching Engine for AgriNegotiator.
Your goal is to match this listing:
Crop: {crop}
Quantity: {quantity} kg
Min Price: ₹{min_price}/kg
Location: {location}

Against these available buyer profiles:
{buyers}

Rank the top 3 best match buyer IDs and explain the matching logic. Mention distance factors, budget compatibility, and strategic fit.
"""
)

# --- Farmer Prompt ---
FARMER_PROMPT = PromptTemplate(
    input_variables=["crop", "quantity", "min_price", "location", "shelf_life", "market_price", "buyer_offer", "round", "history"],
    template="""You are an agricultural producer in Maharashtra, India.
Farmer Profile:
- Crop: {crop}
- Quantity: {quantity} kg
- Target/Min price: ₹{min_price}/kg
- Location: {location}
- Shelf Life: {shelf_life} days
- Current Market Price: ₹{market_price}/kg

Current Negotiation State:
- Round: {round}
- Latest Buyer Offer: ₹{buyer_offer}/kg
- History of negotiation:
{history}

Decide what to do. Options:
- ACCEPT: If the offer is above or very close to target price, or if shelf life is short and you have no time.
- COUNTER: Propose a counter-offer price. Do not go below min price unless critical spoilage (shelf life <= 2 days).
- REJECT: Walk away from this buyer.

Respond STRICTLY in JSON format with keys:
{{"decision": "ACCEPT|COUNTER|REJECT", "counter_price": <number|null>, "reason": "Short strategy reasoning in 1 sentence."}}
"""
)

# --- Buyer Prompt ---
BUYER_PROMPT = PromptTemplate(
    input_variables=["buyer_name", "target_price", "budget", "max_quantity", "location", "farmer_ask", "round", "history"],
    template="""You are the Buyer: {buyer_name}.
Buyer Profile:
- Target Price: ₹{target_price}/kg
- Budget: ₹{budget}
- Max Quantity: {max_quantity} kg
- Location: {location}

Current Negotiation State:
- Round: {round}
- Farmer ask/counter: ₹{farmer_ask}/kg
- History:
{history}

Decide your move. Options:
- ACCEPT: If the farmer's ask matches or is below your budget/target price.
- COUNTER: Propose a counter-offer. Conform to budget constraints (budget / quantity).
- REJECT: Walk away.

Respond STRICTLY in JSON format with keys:
{{"decision": "ACCEPT|COUNTER|REJECT", "counter_price": <number|null>, "reason": "Short reasoning in 1 sentence."}}
"""
)

# --- Validator Prompt ---
VALIDATOR_PROMPT = PromptTemplate(
    input_variables=["farmer_price", "buyer_price", "min_price", "budget", "quantity"],
    template="""You are the Negotiation Validator.
Evaluate the current proposed deal terms:
Farmer Price Ask: ₹{farmer_price}/kg
Buyer Offer: ₹{buyer_price}/kg
Minimum Viable Price: ₹{min_price}/kg
Buyer Budget Limit: ₹{budget}
Quantity: {quantity} kg

Check:
1. Is the deal price within the buyer's budget limit? (Price * Quantity <= Budget)
2. Does the deal price satisfy the farmer's minimum requirements? (If price < Min Price, is it justified by spoilage?)
3. Are the prices converged? (Within 5% gap)

Respond STRICTLY in JSON:
{{"valid": true|false, "reason": "Detailed validation outcome check."}}
"""
)

# --- Reflection Prompt ---
REFLECTION_PROMPT = PromptTemplate(
    input_variables=["crop", "status", "rounds", "history", "summary"],
    template="""You are the Negotiation Reflection Agent.
Review the completed/failed negotiation for {crop}.
Status: {status}
Rounds elapsed: {rounds}
Summary of outcome: {summary}

Negotiation Log:
{history}

Provide a concise post-mortem analysis (2-3 sentences). Highlight:
1. Negotiation efficiency and convergence behavior.
2. Fairness of the final price relative to market price.
3. Recommendation for future matching or fallback strategy improvement.
"""
)
