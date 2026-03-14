import os
import json
import time

from dotenv import load_dotenv
from openai import OpenAI


# ----------------------------------------
# Load environment variables
# ----------------------------------------

load_dotenv()

API_KEY = os.getenv("FEATHERLESS_API_KEY")
BASE_URL = os.getenv("FEATHERLESS_BASE_URL")


# ----------------------------------------
# LLM Client
# ----------------------------------------

class LLMClient:

    def __init__(self):

        if not API_KEY:
            raise ValueError("FEATHERLESS_API_KEY not found in .env")

        self.client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL
        )

        # Model choices
        self.reasoning_model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
        self.fast_model = "mistralai/Mistral-7B-Instruct-v0.2"

    # ----------------------------------------
    # Basic prompt request
    # ----------------------------------------

    def generate_response(self, prompt, model=None, temperature=0.7):

        if model is None:
            model = self.fast_model

        try:

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature
            )

            return response.choices[0].message.content

        except Exception as e:

            print("LLM Error:", e)
            return None

    # ----------------------------------------
    # Negotiation reasoning
    # ----------------------------------------

    def negotiation_reasoning(
        self,
        role,
        offered_price,
        target_price,
        market_price,
        quantity
    ):

        prompt = f"""
You are an AI agent participating in an agricultural market negotiation.

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

If countering, suggest a new price.

Respond ONLY in JSON format:

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

        try:
            result = json.loads(raw)
            return result

        except:

            # fallback parsing
            return {
                "decision": "COUNTER",
                "counter_price": market_price,
                "reason": "fallback decision"
            }

    # ----------------------------------------
    # Strategy analysis
    # ----------------------------------------

    def analyze_strategy(
        self,
        negotiation_history
    ):

        prompt = f"""
You are analyzing a negotiation between agents.

Negotiation history:
{negotiation_history}

Analyze:

1. Is the deal fair?
2. Who has stronger bargaining power?
3. Suggest best next move.

Respond in plain text.
"""

        return self.generate_response(
            prompt,
            model=self.reasoning_model,
            temperature=0.4
        )

    # ----------------------------------------
    # Market reasoning
    # ----------------------------------------

    def market_analysis(
        self,
        demand_level,
        supply_level,
        market_price
    ):

        prompt = f"""
You are analyzing agricultural market conditions.

Demand level: {demand_level}
Supply level: {supply_level}
Current market price: ₹{market_price}/kg

Explain the market situation briefly and suggest pricing strategy.
"""

        return self.generate_response(
            prompt,
            model=self.fast_model,
            temperature=0.5
        )

    # ----------------------------------------
    # Retry-safe request
    # ----------------------------------------

    def safe_request(self, prompt, retries=3):

        for i in range(retries):

            result = self.generate_response(prompt)

            if result:
                return result

            time.sleep(2)

        return None


# ----------------------------------------
# Simple test
# ----------------------------------------

if __name__ == "__main__":

    llm = LLMClient()

    test = llm.negotiation_reasoning(
        role="Farmer",
        offered_price=18,
        target_price=22,
        market_price=20,
        quantity=500
    )

    print("\nLLM Decision:\n")
    print(test)