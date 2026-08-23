"""Telethon client construction."""

from __future__ import annotations

from telethon import TelegramClient
from telethon.sessions import StringSession

from app.core.config import Settings


def build_user_client(
    session_str: str | None, settings: Settings
) -> TelegramClient:
    """Create a user-account client from a (possibly empty) session string."""
    return TelegramClient(
        StringSession(session_str or ""),
        settings.telegram_api_id,
        settings.telegram_api_hash,
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
        device_model="TelegramSaaSCentral",
    )
    client.session = StringSession()
    return client


async def start_bot_client(client: TelegramClient, token: str) -> TelegramClient:
    """Start and authorize a bot client."""
    await client.start(bot_token=token)
    return client
