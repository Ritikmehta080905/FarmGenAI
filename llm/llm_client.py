"""
llm/llm_client.py â€” Unified LLM interface for AgriNegotiator.

All agent code that needs AI reasoning should import from here.
Falls back to None silently when no credentials are configured.

Primary API:
    client = LLMClient()
    text = client.generate(prompt)               # basic completion
    result = client.negotiation_reasoning(...)    # structured JSON
"""

import json
import os
import re
import time

from dotenv import load_dotenv

load_dotenv(override=False)

API_KEY: str = os.getenv("FEATHERLESS_API_KEY", "")
BASE_URL: str = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")
ENABLE_LLM: bool = os.getenv("ENABLE_LLM", "false").lower() in {"1", "true", "yes"}


class LLMClient:
    """Unified LLM client with safe fallback."""

    def __init__(self):
        self.enabled = bool(API_KEY) and ENABLE_LLM
        self._client = None
        self.reasoning_model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
        self.fast_model = "mistralai/Mistral-7B-Instruct-v0.2"

        if self.enabled:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
            except Exception:
                self.enabled = False

    # ------------------------------------------------------------------ #
    #  Core completion                                                     #
    # ------------------------------------------------------------------ #

    def generate(self, prompt: str, model: str = None, temperature: float = 0.7,
                 max_tokens: int = 200) -> str | None:
        """Return raw completion text or None if unavailable."""
        if not self._client:
            return None
        model = model or self.fast_model
        try:
            resp = self._client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=6,
            )
            return resp.choices[0].message.content
        except Exception:
            return None

    # Alias for backward-compat
    def generate_response(self, prompt, model=None, temperature=0.7, max_tokens=200):
        return self.generate(prompt, model=model, temperature=temperature,
                             max_tokens=max_tokens)

    def get_completion(self, prompt, model=None, temperature=0.7, max_tokens=200):
        return self.generate(prompt, model=model, temperature=temperature,
                             max_tokens=max_tokens)

    # ------------------------------------------------------------------ #
    #  Structured negotiation reasoning                                   #
    # ------------------------------------------------------------------ #

    def negotiation_reasoning(
        self, role: str, offered_price: float, target_price: float,
        market_price: float, quantity: float
    ) -> dict:
        """
        Ask the LLM for ACCEPT / COUNTER / REJECT decision.
        Returns dict with keys: decision, counter_price, reason.
        Falls back to deterministic logic when LLM is unavailable.
        """
        prompt = f"""
You are an AI agent in an agricultural market negotiation.
Role: {role}
Current offer price: â‚¹{offered_price}/kg
Target price: â‚¹{target_price}/kg
Market price: â‚¹{market_price}/kg
Quantity: {quantity} kg

Decide what to do next.
Possible decisions: ACCEPT, COUNTER, REJECT

Respond STRICTLY in JSON:
{{"decision": "ACCEPT|COUNTER|REJECT", "counter_price": <number|null>, "reason": "..."}}
"""
        raw = self.generate(prompt, model=self.reasoning_model,
                            temperature=0.3, max_tokens=150)

        if raw:
            try:
                m = re.search(r"\{.*\}", raw, re.DOTALL)
                if m:
                    return json.loads(m.group())
            except (json.JSONDecodeError, Exception):
                pass

        # deterministic fallback
        if offered_price >= target_price:
            return {"decision": "ACCEPT", "counter_price": None,
                    "reason": "Price meets target"}
        gap = target_price - offered_price
        counter = round(offered_price + gap * 0.4, 2)
        return {"decision": "COUNTER", "counter_price": counter,
                "reason": "fallback counter"}

    # ------------------------------------------------------------------ #
    #  Analysis helpers                                                   #
    # ------------------------------------------------------------------ #

    def analyze_strategy(self, negotiation_history) -> str | None:
        prompt = (
            f"Analyze this agricultural negotiation:\n{negotiation_history}\n"
            "1. Is the deal fair?  2. Bargaining power?  3. Best next move?"
        )
        return self.generate(prompt, model=self.reasoning_model,
                             temperature=0.4, max_tokens=200)

    def market_analysis(self, demand_level, supply_level, market_price) -> str | None:
        prompt = (
            f"Agricultural market: demand={demand_level}, supply={supply_level},"
            f" price=â‚¹{market_price}/kg. Provide brief analysis."
        )
        return self.generate(prompt, model=self.fast_model,
                             temperature=0.5, max_tokens=150)

    def safe_request(self, prompt: str, retries: int = 3) -> str | None:
        for _ in range(retries):
            result = self.generate(prompt)
            if result:
                return result
            time.sleep(2)
        return None


# Module-level singleton â€” import and use directly
client: LLMClient = LLMClient()
