"""
intelligence/llm_client.py â€” backward-compat re-export from llm/llm_client.py.

Agents import LLMClient from here; the actual implementation lives in
llm/llm_client.py (the unified interface).
"""

from llm.llm_client import LLMClient, client  # noqa: F401 â€” re-export

__all__ = ["LLMClient", "client"]
