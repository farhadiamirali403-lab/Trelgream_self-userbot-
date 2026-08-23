"""Telegram account and (encrypted) session models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, int_pk


class TelegramAccount(Base, TimestampMixin):
    """A Telegram account linked to a platform user (phone-level auth)."""

    __tablename__ = "telegram_accounts"

    id: Mapped[int] = int_pk()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)

    is_authorized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Free-form auth state string (e.g. "awaiting_code", "awaiting_2fa", "authorized").
    auth_state: Mapped[str] = mapped_column(String(32), default="created", nullable=False)
    last_code_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="telegram_accounts")  # noqa: F821
    sessions: Mapped[list["TelegramSession"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    userbots: Mapped[list["Userbot"]] = relationship(back_populates="account")  # noqa: F821


class TelegramSession(Base, TimestampMixin):
    """Encrypted-at-rest Telegram session. Raw session must NEVER be stored here."""

    __tablename__ = "telegram_sessions"

    id: Mapped[int] = int_pk()
    telegram_account_id: Mapped[int] = mapped_column(
        ForeignKey("telegram_accounts.id", ondelete="CASCADE"), index=True
    )

    # Ciphertext produced by app.core.security.SessionCipher.
    encrypted_session: Mapped[str] = mapped_column(Text, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Device fingerprint (non-sensitive metadata).
    device_model: Mapped[str | None] = mapped_column(String(128))
    device_app: Mapped[str | None] = mapped_column(String(128))
    ip_hint: Mapped[str | None] = mapped_column(String(64))

    account: Mapped["TelegramAccount"] = relationship(back_populates="sessions")
