"""
llm/featherless_client.py — Thin wrapper around the Featherless.ai API.

This is kept intentionally simple.  The main LLMClient (llm/llm_client.py)
bundles everything needed; use this only if you need direct Featherless access.
"""

import os
from dotenv import load_dotenv

load_dotenv(override=False)

API_KEY = os.getenv("FEATHERLESS_API_KEY", "")
BASE_URL = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")


def ask_featherless(prompt: str, model: str = "mistralai/Mistral-7B-Instruct-v0.2",
                   temperature: float = 0.7, max_tokens: int = 200) -> str | None:
    """Send a prompt to Featherless and return the response text, or None."""
    if not API_KEY:
        return None
    try:
        from openai import OpenAI
        c = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        resp = c.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=6,
        )
        return resp.choices[0].message.content
    except Exception:
        return None
