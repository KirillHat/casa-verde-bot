"""Typed application configuration loaded from environment variables.

All settings are validated by pydantic-settings at startup so missing required
values fail fast (with a clear error) instead of crashing mid-request.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ScoreLabel = Literal["HOT", "WARM", "COLD"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Twilio ------------------------------------------------------------
    twilio_account_sid: str
    twilio_auth_token: SecretStr
    twilio_whatsapp_from: str = "whatsapp:+14155238886"

    # ---- Claude ------------------------------------------------------------
    anthropic_api_key: SecretStr
    claude_model: str = "claude-sonnet-4-6"
    claude_max_tokens: int = 1024

    # ---- Google Sheets (optional — leave empty to disable CRM sync) --------
    google_credentials_json: Path = Path("./google_credentials.json")
    google_sheets_id: str = ""
    google_sheets_tab: str = "Leads"

    # ---- Slack -------------------------------------------------------------
    slack_webhook_url: SecretStr | None = None
    slack_notify_enabled: bool = True
    slack_notify_min_score: ScoreLabel = "WARM"

    # ---- App ---------------------------------------------------------------
    app_base_url: str = "http://localhost:8000"
    database_url: str = "sqlite+aiosqlite:///./data/leads.db"
    log_level: str = "INFO"
    environment: str = "development"
    debug_skip_twilio_signature: bool = False

    # ---- Sentry ------------------------------------------------------------
    sentry_dsn: str | None = None

    # ---- Business config ---------------------------------------------------
    business_name: str = "Casa Verde Realty"
    business_timezone: str = "America/Los_Angeles"
    business_phone_display: str = "+1 (310) 555-0142"
    lead_score_hot_threshold: int = Field(default=80, ge=0, le=200)
    lead_score_warm_threshold: int = Field(default=50, ge=0, le=200)


@lru_cache
def get_settings() -> Settings:
    """Return a singleton Settings instance.

    `lru_cache` makes this safe to call from anywhere; tests can call
    `get_settings.cache_clear()` to pick up new env vars.
    """
    return Settings()
