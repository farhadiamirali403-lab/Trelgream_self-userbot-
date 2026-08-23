"""Userbot instance model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, int_pk


class Userbot(Base, TimestampMixin):
    __tablename__ = "userbots"

    id: Mapped[int] = int_pk()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    telegram_account_id: Mapped[int] = mapped_column(
        ForeignKey("telegram_accounts.id", ondelete="CASCADE"), index=True
    )

    name: Mapped[str | None] = mapped_column(String(128))

    # Lifecycle: CREATED/AUTHENTICATING/AUTHORIZED/STARTING/RUNNING/
    #            STOPPING/STOPPED/ERROR/RECOVERING/SUSPENDED
    status: Mapped[str] = mapped_column(String(32), default="CREATED", nullable=False, index=True)

    current_worker_id: Mapped[int | None] = mapped_column(
        ForeignKey("workers.id", ondelete="SET NULL"), index=True
    )
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(String(512))

    user: Mapped["User"] = relationship(back_populates="userbots")  # noqa: F821
    account: Mapped["TelegramAccount"] = relationship(back_populates="userbots")  # noqa: F821
    worker: Mapped["Worker"] = relationship(back_populates="userbots")  # noqa: F821
