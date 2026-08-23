"""Scheduled task service: creation and repeat-rule computation."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.scheduler import ScheduledTask
from app.scheduler.repository import ScheduledTaskRepository


def next_run_after(run_at: datetime, repeat_rule: str | None) -> datetime | None:
    """Compute the next run time for a repeat rule, or None for one-time tasks."""
    if not repeat_rule or repeat_rule == "one_time":
        return None
    if repeat_rule == "daily":
        return run_at + timedelta(days=1)
    if repeat_rule == "weekly":
        return run_at + timedelta(days=7)
    if repeat_rule == "monthly":
        return run_at + timedelta(days=30)
    if repeat_rule == "hourly":
        return run_at + timedelta(hours=1)
    if repeat_rule.startswith("interval:"):
        try:
            seconds = int(repeat_rule.split(":", 1)[1])
            return run_at + timedelta(seconds=seconds)
        except ValueError:
            return None
    return None


class ScheduledTaskService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ScheduledTaskRepository(session)

    async def create(
        self,
        user_id: int,
        *,
        type_: str,
        payload: dict,
        run_at: datetime,
        repeat_rule: str | None = "one_time",
    ) -> ScheduledTask:
        task = ScheduledTask(
            user_id=user_id,
            type=type_,
            payload=payload,
            run_at=run_at,
            repeat_rule=repeat_rule,
            status="pending",
            next_run_at=run_at,
        )
        return await self.repo.add(task)

    async def list_for_user(self, user_id: int) -> list[ScheduledTask]:
        return await self.repo.list_for_tenant(user_id)

    async def cancel(self, user_id: int, task_id: int) -> ScheduledTask:
        task = await self.repo.get_for_tenant(task_id, user_id)
        task.status = "cancelled"
        await self.repo.session.flush()
        return task

    @staticmethod
    def advance(task: ScheduledTask, now: datetime) -> None:
        """Mark a finished task and schedule its next occurrence (idempotent)."""
        task.last_run_at = now
        task.retry_count = 0
        nxt = next_run_after(now, task.repeat_rule)
        if nxt is None:
            task.status = "success"
            task.next_run_at = None
        else:
            task.status = "pending"
            task.next_run_at = nxt
