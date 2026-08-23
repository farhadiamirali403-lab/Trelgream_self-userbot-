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
    # Optional proxy (e.g. "socks5://127.0.0.1:1080" or "http://host:port")
    telegram_proxy: str = ""

    # --- Security ---
    session_encryption_key: str = ""
    admin_api_key: str = ""

    # --- Web ---
    # آدرس عمومی بک‌اند برای لینک احراز هویت وب (مثلاً http://192.168.1.10:8000).
    # اگر خالی باشد، IP محلی به‌صورت خودکار تشخیص داده می‌شود.
    web_base_url: str = ""
    backend_port: int = 8000

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

    def resolve_web_base_url(self) -> str:
        """Return the reachable base URL for the web auth page.

        Uses ``web_base_url`` when set, otherwise auto-detects the LAN IP so
        the link works from other computers on the same network.
        """
        if self.web_base_url:
            return self.web_base_url.rstrip("/")
        return f"http://{get_lan_ip()}:{self.backend_port}"


def get_lan_ip() -> str:
    """Detect the primary LAN IPv4 address (falls back to 127.0.0.1)."""
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # UDP connect does not send packets; it only selects the route.
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:  # noqa: BLE001
        return "127.0.0.1"
    finally:
        s.close()


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()
