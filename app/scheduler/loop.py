"""Scheduler main loop: subscription expiration + due scheduled tasks."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.billing.service import BillingService
from app.core.config import Settings
from app.core.logging import get_logger
from app.core.security import CommandSigner
from app.database.session import async_session_factory
from app.scheduler.queue import TaskQueue
from app.scheduler.repository import ScheduledTaskRepository
from app.scheduler.service import ScheduledTaskService

log = get_logger("scheduler")


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def run_scheduler(settings: Settings, signer: CommandSigner) -> None:
    """Run the scheduler loop until cancelled."""
    from app.core.redis import get_redis

    redis = get_redis()
    task_queue = TaskQueue(redis, signer)

    log.info("Scheduler starting", extra_fields={"tick": settings.scheduler_tick_seconds})
    while True:
        async with async_session_factory() as session:
            try:
                billing = BillingService(session)
                expired = await billing.expire_due_subscriptions()
                if expired:
                    log.info("subscriptions expired", extra_fields={"count": expired})

                await _dispatch_due_tasks(session, task_queue)
                await session.commit()
            except Exception as exc:  # noqa: BLE001
                await session.rollback()
                log.error("scheduler tick failed", extra_fields={"error": str(exc)})
        await asyncio.sleep(settings.scheduler_tick_seconds)


async def _dispatch_due_tasks(session, task_queue: TaskQueue) -> None:
    repo = ScheduledTaskRepository(session)
    service = ScheduledTaskService(session)
    now = _now()
    due = await repo.list_due(now)
    for task in due:
        # Idempotent: a task is dispatched exactly once per run window.
        await task_queue.enqueue(
            task.id, task.user_id, task.type, task.payload or {}
        )
        service.advance(task, now)
    await session.flush()
