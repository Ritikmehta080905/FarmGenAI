"""Central runtime settings.  Values are read from environment / .env file."""

import os
from dotenv import load_dotenv

load_dotenv(override=False)

# ── LLM ─────────────────────────────────────────────────────────
ENABLE_LLM: bool = os.getenv("ENABLE_LLM", "false").lower() in {"1", "true", "yes"}
FEATHERLESS_API_KEY: str = os.getenv("FEATHERLESS_API_KEY", "")
FEATHERLESS_BASE_URL: str = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")
DEFAULT_LLM_MODEL: str = os.getenv("LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")

# ── Server ───────────────────────────────────────────────────────
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))

WS_HOST: str = os.getenv("WS_HOST", "localhost")
WS_PORT: int = int(os.getenv("WS_PORT", "8765"))

# ── Database ─────────────────────────────────────────────────────
DB_PATH: str = os.getenv("DB_PATH", "agrinegotiator.db")

# ── Simulation ───────────────────────────────────────────────────
DEFAULT_MAX_ROUNDS: int = int(os.getenv("DEFAULT_MAX_ROUNDS", "5"))
