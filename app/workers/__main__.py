"""Worker manager process entry point: python -m app.workers"""

from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.core.eventloop import configure_event_loop
from app.core.logging import configure_logging
from app.core.redis import get_redis
from app.core.security import CommandSigner, SessionCipher
from app.scheduler.queue import TaskQueue
from app.workers.commands import CommandBus
from app.workers.manager import WorkerManager


def main() -> None:
    configure_event_loop()
    settings = get_settings()
    configure_logging("INFO", settings.debug)
    settings.ensure_telegram_credentials()

    # Import to populate the module registry.
    import app.modules.builtin  # noqa: F401
    from app.modules.registry import registry

    redis = get_redis()
    cipher = SessionCipher(settings.session_encryption_key)
    signer = CommandSigner(settings.session_encryption_key or "worker")
    command_bus = CommandBus(redis, signer)
    task_queue = TaskQueue(redis, signer)

    manager = WorkerManager(settings, cipher, command_bus, registry, task_queue)
    try:
        asyncio.run(manager.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
