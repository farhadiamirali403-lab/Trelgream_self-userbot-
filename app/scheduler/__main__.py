"""Scheduler process entry point: python -m app.scheduler"""

from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.core.eventloop import configure_event_loop
from app.core.logging import configure_logging
from app.core.security import CommandSigner
from app.scheduler.loop import run_scheduler


def main() -> None:
    configure_event_loop()
    settings = get_settings()
    configure_logging("INFO", settings.debug)
    signer = CommandSigner(settings.session_encryption_key or "scheduler")
    try:
        asyncio.run(run_scheduler(settings, signer))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
