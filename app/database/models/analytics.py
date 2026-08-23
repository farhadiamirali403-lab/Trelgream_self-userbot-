"""Usage metric model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, int_pk


class UsageMetric(Base):
    __tablename__ = "usage_metrics"

    id: Mapped[int] = int_pk()
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    metric_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # messages, ...
    value: Mapped[float] = mapped_column(Float, default=0.0)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
