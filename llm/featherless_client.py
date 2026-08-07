"""
llm/featherless_client.py — Deprecated. Replaced by LLMClient using Ollama and Gemini.
"""

from llm.llm_client import client


def ask_featherless(prompt: str, **kwargs) -> str | None:
    """Deprecated alias — routes directly to LLMClient."""
    return client.generate(prompt, **kwargs)
