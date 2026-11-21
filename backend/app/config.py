"""Central configuration, loaded from environment / .env.

Nothing here requires credentials: with STUDENT_OS_MOCK=true (the default)
the whole system runs on realistic sample data.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root = two levels up from this file (backend/app/config.py -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    # Load the .env at the repo root; ignore unknown keys.
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Global
    student_os_mock: bool = True

    # LLM (Gemini / Anthropic)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-lite-latest"
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-5"

    # GitHub
    github_token: str = ""

    # Codeforces
    codeforces_handle: str = ""

    # Google
    google_client_id: str = ""
    google_client_secret: str = ""
    google_oauth_redirect: str = "http://localhost:8000/auth/google/callback"

    # Backend server
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    # Security & JWT
    jwt_secret_key: str = "kairo-jwt-secret-key-change-in-production-2026"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Caching. Redis when set + reachable, else in-memory (see app/cache.py).
    redis_url: str = ""
    cache_ttl_seconds: int = 90

    # Persistence. SQLite by default (zero setup); set DATABASE_URL to a
    # postgresql://... string to use Postgres instead. See app/store.py.
    database_url: str = ""
    persist_enabled: bool = True

    # Which ranker the runtime uses: "rule" (baseline) or "learned".
    ranker: str = "rule"

    # Notifications (all optional — with none set, the notifier is dry-run).
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notify_email_to: str = ""

    # Study-material notes directory for the RAG assistant.
    study_notes_dir: str = ""

    @property
    def resolved_database_url(self) -> str:
        return self.database_url or f"sqlite:///{BACKEND_ROOT / 'student_os.db'}"

    @property
    def resolved_study_notes_dir(self) -> str:
        return self.study_notes_dir or str(BACKEND_ROOT / "eval" / "rag_corpus")

    # Path to the MCP server registry.
    servers_config: Path = BACKEND_ROOT / "servers.json"

    @property
    def llm_enabled(self) -> bool:
        """True when a real LLM should be used instead of the rule-based planner."""
        return bool(self.gemini_api_key or self.anthropic_api_key) and not self.student_os_mock


@lru_cache
def get_settings() -> Settings:
    return Settings()
