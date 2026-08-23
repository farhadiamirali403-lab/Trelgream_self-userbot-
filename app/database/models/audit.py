"""Audit, system and error log models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, JSONType, int_pk


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = int_pk()
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    actor_id: Mapped[int | None] = mapped_column(BigInteger, index=True)  # admin.id
    actor_role: Mapped[str | None] = mapped_column(String(32))

    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)  # APPROVE_PAYMENT
    target_type: Mapped[str | None] = mapped_column(String(64))
    target_id: Mapped[str | None] = mapped_column(String(64))

    result: Mapped[str] = mapped_column(String(32), default="SUCCESS")  # SUCCESS/FAILURE
    meta: Mapped[dict | None] = mapped_column(JSONType)


class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = int_pk()
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(16), default="INFO")
    component: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSONType)


class ErrorLog(Base):
    __tablename__ = "error_logs"

    id: Mapped[int] = int_pk()
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(16), default="ERROR")
    component: Mapped[str] = mapped_column(String(64), index=True)
    exception: Mapped[str | None] = mapped_column(String(255))
    traceback: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSONType)
