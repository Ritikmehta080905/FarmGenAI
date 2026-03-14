import json
import os
import time

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

API_KEY = os.getenv("FEATHERLESS_API_KEY")
BASE_URL = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")
ENABLE_LLM = os.getenv("ENABLE_LLM", "false").lower() in {"1", "true", "yes"}


class LLMClient:
    """LLM wrapper with safe fallback when remote models are unavailable."""

    def __init__(self):
        self.enabled = bool(API_KEY) and ENABLE_LLM
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL) if self.enabled else None
        self.reasoning_model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
        self.fast_model = "mistralai/Mistral-7B-Instruct-v0.2"

    def get_completion(self, prompt, model=None, temperature=0.7, max_tokens=200):
        return self.generate_response(prompt, model=model, temperature=temperature, max_tokens=max_tokens)

    def generate_response(self, prompt, model=None, temperature=0.7, max_tokens=200):
        model = model or self.fast_model
        if not self.client:
            return None

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=6,
            )
            return response.choices[0].message.content
        except Exception:
            return None

    def negotiation_reasoning(self, role, offered_price, target_price, market_price, quantity):
        prompt = f"""
You are an AI agent participating in an agricultural market negotiation.

Role: {role}
Current offer price: Rs.{offered_price}/kg
Target price: Rs.{target_price}/kg
Market price: Rs.{market_price}/kg
Quantity: {quantity} kg

Possible decisions:
ACCEPT
COUNTER
REJECT

Respond ONLY in JSON format:
{{
 "decision": "ACCEPT | COUNTER | REJECT",
 "counter_price": number or null,
 "reason": "short explanation"
}}
"""

        raw = self.generate_response(prompt, model=self.reasoning_model, temperature=0.3, max_tokens=150)
        if raw is None:
            return {
                "decision": "COUNTER",
                "counter_price": market_price,
                "reason": "LLM unavailable; using fallback"
            }

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "decision": "COUNTER",
                "counter_price": market_price,
                "reason": "fallback decision due to parsing error"
            }

    def analyze_strategy(self, negotiation_history):
        prompt = f"""
You are analyzing a negotiation between agents.

Negotiation history:
{negotiation_history}

Analyze:
1. Is the deal fair?
2. Who has stronger bargaining power?
3. Suggest best next move.
"""
        return self.generate_response(prompt, model=self.reasoning_model, temperature=0.4, max_tokens=200)

    def market_analysis(self, demand_level, supply_level, market_price):
        prompt = f"""
You are analyzing agricultural market conditions.

Demand level: {demand_level}
Supply level: {supply_level}
Current market price: Rs.{market_price}/kg
"""
        return self.generate_response(prompt, model=self.fast_model, temperature=0.5, max_tokens=150)

    def safe_request(self, prompt, retries=3):
        for _ in range(retries):
            result = self.generate_response(prompt)
            if result:
                return result
            time.sleep(2)
        return None
