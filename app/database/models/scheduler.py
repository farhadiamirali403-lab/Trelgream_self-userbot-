"""Scheduled task model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, JSONType, TimestampMixin, int_pk


class ScheduledTask(Base, TimestampMixin):
    __tablename__ = "scheduled_tasks"

    id: Mapped[int] = int_pk()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    type: Mapped[str] = mapped_column(String(64), nullable=False)  # send_message, ...
    payload: Mapped[dict | None] = mapped_column(JSONType)

    run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # one_time / daily / weekly / monthly / cron / interval
    repeat_rule: Mapped[str | None] = mapped_column(String(255))

    # pending/running/success/failed/cancelled
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)

    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
