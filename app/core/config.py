"""Application configuration.

All runtime configuration is loaded from environment variables / ``.env``.
No secrets are ever hardcoded; the ``.env`` file is git-ignored.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root:  app/core/config.py -> app/core -> app -> <root>
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Strongly-typed settings loaded from the environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Environment ---
    app_env: str = "development"
    debug: bool = True

    # --- Infrastructure ---
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/telegram_saas"
    redis_url: str = "redis://localhost:6379/0"

    # --- Telegram credentials ---
    telegram_api_id: int | None = None
    telegram_api_hash: str = ""
    central_bot_token: str = ""

    # --- Security ---
    session_encryption_key: str = ""
    admin_api_key: str = ""

    # --- Owner ---
    owner_telegram_id: int | None = None

    # --- Payment settings ---
    payment_card_number: str = ""
    payment_card_owner: str = ""

    # --- Storage ---
    storage_path: str = "./storage"

    # --- Limits / thresholds ---
    login_rate_limit: int = 5
    code_verify_rate_limit: int = 3
    worker_heartbeat_interval: int = 10
    worker_heartbeat_timeout: int = 60
    scheduler_tick_seconds: int = 60

    # --- Validators ---

    @field_validator("telegram_api_id", "owner_telegram_id", mode="before")
    @classmethod
    def _empty_int_to_none(cls, value: object) -> object:
        if value == "" or value is None:
            return None
        return value

    # --- Convenience properties ---

    @property
    def storage_dir(self) -> Path:
        """Absolute path to the local storage directory."""
        p = Path(self.storage_path)
        return p if p.is_absolute() else BASE_DIR / p

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in {"development", "dev", "local"}

    def ensure_telegram_credentials(self) -> None:
        """Raise early if mandatory Telegram credentials are missing."""
        if not self.telegram_api_id or not self.telegram_api_hash:
            raise RuntimeError(
                "TELEGRAM_API_ID / TELEGRAM_API_HASH تنظیم نشده‌اند. "
                "آن‌ها را در .env قرار دهید."
            )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()
