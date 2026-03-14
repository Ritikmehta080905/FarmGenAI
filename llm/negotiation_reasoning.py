import re
import json

def negotiation_reasoning(
    self,
    role,
    offered_price,
    target_price,
    market_price,
    quantity
):
    prompt = f"""
You are an AI agent in an agricultural market negotiation.

Role: {role}
Current offer price: ₹{offered_price}/kg
Target price: ₹{target_price}/kg
Market price: ₹{market_price}/kg
Quantity: {quantity} kg

Decide what to do next.

Possible decisions:
ACCEPT
COUNTER
REJECT

IMPORTANT: Output must start with '{' and end with '}'. Do not include any text outside JSON.
Use double quotes only.

Respond STRICTLY in JSON format, starting with '{{' and ending with '}}', no extra text:

{{
 "decision": "ACCEPT | COUNTER | REJECT",
 "counter_price": number or null,
 "reason": "short explanation"
}}
"""

    raw = self.generate_response(
        prompt,
        model=self.reasoning_model,
        temperature=0.3
    )

    if raw is None:
        return None

    # -----------------------------
    # Extract JSON from text
    # -----------------------------
    try:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            return result
    except Exception as e:
        print("JSON parsing error:", e)
        print("Raw LLM output:", raw)

    # fallback if still fails
    return {
        "decision": "COUNTER",
        "counter_price": market_price,
        "reason": "fallback decision due to parsing error"
    }