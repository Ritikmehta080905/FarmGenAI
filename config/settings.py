"""Central runtime settings.  Values are read from environment / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── LLM ─────────────────────────────────────────────────────────
    ENABLE_LLM: bool = False
    FEATHERLESS_API_KEY: str = ""
    FEATHERLESS_BASE_URL: str = "https://api.featherless.ai/v1"
    DEFAULT_LLM_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"

    # ── Server ───────────────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    WS_HOST: str = "localhost"
    WS_PORT: int = 8765

    # ── Database & Cache & Search ────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://admin:admin_password@localhost:5433/agrinegotiator"
    REDIS_URL: str = "redis://localhost:6379/0"
    CHROMA_URL: str = "http://localhost:8001"
    OLLAMA_URL: str = "http://localhost:11434"

    # ── Security & Authentication ────────────────────────────────────
    JWT_SECRET_KEY: str = "supersecretkeyforagrinegotiatorsigningtokens12345"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ── Legacy / Simulation ──────────────────────────────────────────
    DB_PATH: str = "agrinegotiator.db"
    DEFAULT_MAX_ROUNDS: int = 5
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"


settings = Settings()

# Export for backward compatibility
ENABLE_LLM = settings.ENABLE_LLM
FEATHERLESS_API_KEY = settings.FEATHERLESS_API_KEY
FEATHERLESS_BASE_URL = settings.FEATHERLESS_BASE_URL
DEFAULT_LLM_MODEL = settings.DEFAULT_LLM_MODEL
API_HOST = settings.API_HOST
API_PORT = settings.API_PORT
WS_HOST = settings.WS_HOST
WS_PORT = settings.WS_PORT
DATABASE_URL = settings.DATABASE_URL
REDIS_URL = settings.REDIS_URL
CHROMA_URL = settings.CHROMA_URL
OLLAMA_URL = settings.OLLAMA_URL
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
DB_PATH = settings.DB_PATH
DEFAULT_MAX_ROUNDS = settings.DEFAULT_MAX_ROUNDS
EMBEDDING_MODEL = settings.EMBEDDING_MODEL

