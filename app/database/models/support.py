"""Notification and support ticket models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, JSONType, TimestampMixin, int_pk


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = int_pk()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    type: Mapped[str] = mapped_column(String(64), nullable=False)  # payment_approved, ...
    content: Mapped[dict | None] = mapped_column(JSONType)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SupportTicket(Base, TimestampMixin):
    __tablename__ = "support_tickets"

    id: Mapped[int] = int_pk()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # open/answered/closed
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
