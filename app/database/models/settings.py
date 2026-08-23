"""System settings and payment settings models."""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, JSONType, TimestampMixin, int_pk


class Setting(Base, TimestampMixin):
    __tablename__ = "settings"

    id: Mapped[int] = int_pk()
    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    value: Mapped[dict | None] = mapped_column(JSONType)
    description: Mapped[str | None] = mapped_column(String(255))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)


class PaymentSetting(Base, TimestampMixin):
    __tablename__ = "payment_settings"

    id: Mapped[int] = int_pk()
    card_number: Mapped[str] = mapped_column(String(32), default="")
    card_owner: Mapped[str] = mapped_column(String(128), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
