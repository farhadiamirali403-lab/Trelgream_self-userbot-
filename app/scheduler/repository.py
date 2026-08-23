"""Scheduled task repository."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.scheduler import ScheduledTask
from app.database.repository import BaseRepository


class ScheduledTaskRepository(BaseRepository[ScheduledTask]):
    model = ScheduledTask

    async def list_due(self, now: datetime, *, limit: int = 500) -> list[ScheduledTask]:
        stmt = (
            select(ScheduledTask)
            .where(
                ScheduledTask.status == "pending",
                ScheduledTask.next_run_at.is_not(None),
                ScheduledTask.next_run_at <= now,
            )
            .order_by(ScheduledTask.next_run_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
