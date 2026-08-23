"""Declarative base and shared column mixins (SQLAlchemy 2.0 style)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# JSON type that uses PostgreSQL JSONB when available and generic JSON otherwise
# (keeps the same models usable in SQLite-based tests).
JSONType = JSON().with_variant(JSONB(), "postgresql")

# Primary key: BIGINT on PostgreSQL, INTEGER on SQLite (so autoincrement works).
PKType = BigInteger().with_variant(Integer, "sqlite")


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def int_pk() -> Mapped[int]:
    """Auto-incrementing bigint primary key."""
    return mapped_column(PKType, primary_key=True, autoincrement=True)


class TimestampMixin:
    """Adds created_at / updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
