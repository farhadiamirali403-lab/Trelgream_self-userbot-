"""User (tenant root) model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, int_pk


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = int_pk()
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), index=True)
    first_name: Mapped[str | None] = mapped_column(String(128))
    last_name: Mapped[str | None] = mapped_column(String(128))
    phone: Mapped[str | None] = mapped_column(String(32), index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    telegram_accounts: Mapped[list["TelegramAccount"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    userbots: Mapped[list["Userbot"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
