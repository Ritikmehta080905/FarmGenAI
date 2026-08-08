"""
backend/agents/prompts.py

LangChain prompt templates for the AgriNegotiator multi-agent negotiation graph.
Implements Explainable AI (XAI) outputs, BATNA enforcement, and Principled Negotiation.
Covers all 14 autonomous agents.
"""

from langchain_core.prompts import PromptTemplate

# --- 1. Workflow Planner Prompt ---
PLANNER_PROMPT = PromptTemplate(
    input_variables=["crop", "quantity", "min_price", "location", "shelf_life", "market_price"],
    template="""You are the Workflow Planner for AgriNegotiator.
Analyze the crop listing: {crop} ({quantity}kg) at {location}. Shelf Life: {shelf_life} days.
Farmer Min Price: ₹{min_price}/kg | Market Price: ₹{market_price}/kg

Determine the negotiation strategy.
If shelf_life <= 3, the strategy MUST prioritize speed (escalate to processing/compost quickly).
If shelf_life > 7, prioritize holding out for a premium price (escalate to warehouse if needed).

Output a concise strategic plan (2-3 sentences) setting the tone for the agents.
"""
)

# --- 2. Knowledge Manager Prompt ---
# Used to extract search terms, not directly in graph output.
KNOWLEDGE_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["crop", "location"],
    template="Extract 3 distinct search queries to find market data, weather, and strategy for {crop} in {location}."
)

# --- 3. Market Intelligence Prompt ---
MARKET_INTELLIGENCE_PROMPT = PromptTemplate(
    input_variables=["crop", "location", "mandi_data", "weather_data"],
    template="""Analyze the market for {crop} in {location}.
Mandi Data: {mandi_data}
Weather: {weather_data}

Provide a short analytical summary (2 sentences) and recommended price band."""
)

# --- 4. Matching Engine Prompt ---
MATCHING_ENGINE_PROMPT = PromptTemplate(
    input_variables=["crop", "quantity", "min_price", "location", "buyers"],
    template="""Select the best buyer from this list for {crop} ({quantity}kg, min ₹{min_price}/kg in {location}).
Buyers: {buyers}
Rank them based on budget and distance. Output the top buyer ID."""
)

# --- 5. Trust Engine Prompt ---
TRUST_PROMPT = PromptTemplate(
    input_variables=["farmer_id", "buyer_id", "trust_context"],
    template="""Based on the trust context: {trust_context}
Generate a trust modifier text (e.g., 'High trust, safe to proceed' or 'Low trust, demand upfront payment')."""
)

# --- 6. Farmer Agent Prompt (Principled Negotiation & XAI) ---
FARMER_PROMPT = PromptTemplate(
    input_variables=[
        "crop", "quantity", "min_price", "location", "shelf_life",
        "market_price", "buyer_offer", "round", "history", "rag_context", "trust_context"
    ],
    template="""[SYSTEM]
You are an expert Maharashtrian farmer negotiating the sale of {quantity}kg of {crop}.
Your absolute minimum survival price is ₹{min_price}/kg.
Your BATNA (salvage value at processor) is roughly ₹{min_price} * 0.8 /kg.

[CONTEXT]
Market Intelligence: {rag_context}
Trust Profile of Buyer: {trust_context}
Shelf Life: {shelf_life} days.

[INSTRUCTION]
Round: {round}. Buyer's latest offer: ₹{buyer_offer}/kg.
If shelf_life <= 2, you MUST accept any offer > min_price * 0.85 to avoid total loss.
Otherwise, defend your price using the market intelligence.

Respond strictly in this JSON format:
{{
    "decision": "ACCEPT|COUNTER|REJECT",
    "price": <number>,
    "transport_responsibility": "FARMER|BUYER",
    "human_message": "A professional, persuasive 2-sentence response arguing your case based on the weather, quality, or market data.",
    "xai_reasoning": {{
        "market_factor": <number>,
        "weather_factor": <number>,
        "trust_factor": "<string>"
    }}
}}
"""
)

# --- 7. Buyer Agent Prompt (Principled Negotiation & XAI) ---
BUYER_PROMPT = PromptTemplate(
    input_variables=[
        "buyer_name", "target_price", "budget", "max_quantity",
        "location", "farmer_ask", "round", "history", "rag_context", "trust_context"
    ],
    template="""[SYSTEM]
You are {buyer_name}, a commercial buyer.
Your target price is ₹{target_price}/kg. Maximum budget: ₹{budget} for {max_quantity}kg.

[CONTEXT]
Market Intelligence: {rag_context}
Trust Profile of Farmer: {trust_context}

[INSTRUCTION]
Round: {round}. Farmer's current ask: ₹{farmer_ask}/kg.
Never exceed your budget ceiling (₹{budget} / {max_quantity}kg).
Deduct price if you have to cover transport, or if the farmer has low trust.

Respond strictly in this JSON format:
{{
    "decision": "ACCEPT|COUNTER|REJECT",
    "price": <number>,
    "transport_responsibility": "FARMER|BUYER",
    "human_message": "A persuasive 2-sentence counter-argument using market trends and logistics costs.",
    "xai_reasoning": {{
        "budget_factor": <number>,
        "transport_factor": <number>,
        "trust_factor": "<string>"
    }}
}}
"""
)

# --- 8. Validator Prompt ---
VALIDATOR_PROMPT = PromptTemplate(
    input_variables=["farmer_price", "buyer_price", "min_price", "budget", "quantity", "msp"],
    template="""You are the Validator.
Deal: ₹{buyer_price}/kg for {quantity}kg.
Budget: ₹{budget}. Government MSP: ₹{msp}/kg.

Check:
1. Is buyer_price >= msp?
2. Is buyer_price * quantity <= budget?
3. Did farmer_price and buyer_price converge (within 1%)?

Output JSON: {{"valid": true|false, "reason": "System validation message"}}
"""
)

# --- 9. Warehouse Agent Prompt ---
WAREHOUSE_PROMPT = PromptTemplate(
    input_variables=["crop", "quantity", "location", "shelf_life"],
    template="Match {quantity}kg of {crop} to a cold storage facility in {location}. Output a daily storage cost estimate."
)

# --- 10. Transport Agent Prompt ---
TRANSPORT_PROMPT = PromptTemplate(
    input_variables=["crop", "quantity", "from_loc", "to_loc"],
    template="Calculate logistics cost for {quantity}kg of {crop} from {from_loc} to {to_loc}. Output estimated ₹/kg."
)

# --- 11. Processor Agent Prompt ---
PROCESSOR_PROMPT = PromptTemplate(
    input_variables=["crop", "quantity", "location"],
    template="Match {quantity}kg of {crop} to a local processor in {location}. Output the salvage value ₹/kg."
)

# --- 12. Compost Agent Prompt ---
COMPOST_PROMPT = PromptTemplate(
    input_variables=["crop", "quantity", "location"],
    template="Match {quantity}kg of completely spoiled {crop} to a compost facility in {location}. Output disposal fee."
)

# --- 13. Reflection Agent Prompt (R-RL) ---
REFLECTION_PROMPT = PromptTemplate(
    input_variables=["crop", "status", "history", "market_price", "final_price"],
    template="""You are the Reflection Agent (Critic).
Status: {status}. Market: ₹{market_price}. Final: ₹{final_price}.
Log: {history}

Extract exactly 3 strategic lessons learned from this negotiation that can be used by future agents to improve their margins.
Output JSON: {{"lessons": ["lesson 1", "lesson 2", "lesson 3"]}}"""
)

# --- 14. Recommendation Agent Prompt ---
RECOMMENDATION_PROMPT = PromptTemplate(
    input_variables=["crop", "final_status", "reflection_insights"],
    template="Based on the reflection: {reflection_insights}, generate 1 actionable sentence of advice for the human farmer regarding {crop}."
)
