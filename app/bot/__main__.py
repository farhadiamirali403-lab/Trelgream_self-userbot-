"""Central bot process entry point: python -m app.bot"""

from __future__ import annotations

import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession

from app.bot.admin_panel import AdminPanel
from app.bot.bot import CentralBot
from app.core.config import get_settings
from app.core.eventloop import configure_event_loop
from app.core.logging import configure_logging


def main() -> None:
    configure_event_loop()
    settings = get_settings()
    configure_logging("INFO", settings.debug)
    if not settings.central_bot_token:
        raise RuntimeError("CENTRAL_BOT_TOKEN تنظیم نشده است")
    settings.ensure_telegram_credentials()

    client = TelegramClient(
        StringSession(),
        settings.telegram_api_id,
        settings.telegram_api_hash,
        device_model="TelegramSaaSCentral",
    )
    bot = CentralBot(settings, client)
    AdminPanel(settings, client).register()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
