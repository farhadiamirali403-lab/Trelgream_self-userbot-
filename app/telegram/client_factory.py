"""Telethon client construction."""

from __future__ import annotations

from urllib.parse import urlparse

from telethon import TelegramClient
from telethon.sessions import StringSession

from app.core.config import Settings


def parse_proxy(url: str) -> tuple | None:
    """Parse a proxy URL into the tuple Telethon expects, or None.

    Supported schemes: ``socks5://``, ``socks5h://``, ``http://``, ``https://``.
    """
    if not url:
        return None
    parsed = urlparse(url if "://" in url else f"socks5://{url}")
    scheme = parsed.scheme.lower()
    host = parsed.hostname
    port = parsed.port or (1080 if scheme.startswith("socks") else 8080)
    if not host:
        return None
    if scheme in ("socks5", "socks5h", "socks"):
        ptype = "socks5"
    elif scheme in ("http", "https"):
        ptype = "http"
    else:
        return None
    if parsed.username:
        return (ptype, host, port, True, parsed.username, parsed.password or "")
    return (ptype, host, port)


def build_user_client(
    session_str: str | None, settings: Settings
) -> TelegramClient:
    """Create a user-account client from a (possibly empty) session string."""
    return TelegramClient(
        StringSession(session_str or ""),
        settings.telegram_api_id,
        settings.telegram_api_hash,
        proxy=parse_proxy(settings.telegram_proxy),
        device_model="TelegramSaaS",
        system_version="Windows",
        app_version="1.0",
    )


def build_bot_client(token: str, settings: Settings) -> TelegramClient:
    """Create a bot-account client and log in with the bot token."""
    client = TelegramClient(
        StringSession(),
        settings.telegram_api_id,
        settings.telegram_api_hash,
        proxy=parse_proxy(settings.telegram_proxy),
        device_model="TelegramSaaSCentral",
    )
    client.session = StringSession()
    return client


async def start_bot_client(client: TelegramClient, token: str) -> TelegramClient:
    """Start and authorize a bot client."""
    await client.start(bot_token=token)
    return client
