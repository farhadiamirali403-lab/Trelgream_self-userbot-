"""Billing models: plans, subscriptions, payments, receipts."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, JSONType, TimestampMixin, int_pk


class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    id: Mapped[int] = int_pk()
    key: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)  # basic/pro/...
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    price: Mapped[int] = mapped_column(BigInteger, default=0)  # به تومان
    duration_days: Mapped[int] = mapped_column(Integer, default=30)

    max_userbots: Mapped[int] = mapped_column(Integer, default=1)
    max_modules: Mapped[int] = mapped_column(Integer, default=10)
    max_automation_rules: Mapped[int] = mapped_column(Integer, default=5)
    max_scheduled_tasks: Mapped[int] = mapped_column(Integer, default=5)

    # Arbitrary plan limits (max_daily_actions, max_storage, ...).
    limits: Mapped[dict | None] = mapped_column(JSONType)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[int] = int_pk()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="RESTRICT"))

    # pending/active/expired/suspended/cancelled
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    user: Mapped["User"] = relationship(back_populates="subscriptions")  # noqa: F821
    plan: Mapped["Plan"] = relationship(lazy="selectin")
    payments: Mapped[list["Payment"]] = relationship(back_populates="subscription")


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[int] = int_pk()
    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)  # PAY-18372
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="RESTRICT"))
    subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="SET NULL")
    )

    amount: Mapped[int] = mapped_column(BigInteger, default=0)
    # pending/approved/rejected
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(32), default="card", nullable=False)

    reviewed_by: Mapped[int | None] = mapped_column(BigInteger)  # admin.id
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reject_reason: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship()  # noqa: F821
    plan: Mapped["Plan"] = relationship(lazy="selectin")
    subscription: Mapped["Subscription"] = relationship(back_populates="payments")
    receipts: Mapped[list["PaymentReceipt"]] = relationship(
        back_populates="payment", cascade="all, delete-orphan"
    )


class PaymentReceipt(Base, TimestampMixin):
    __tablename__ = "payment_receipts"

    id: Mapped[int] = int_pk()
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), index=True)

    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)  # path/key in storage
    file_name: Mapped[str | None] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(128))
    size: Mapped[int] = mapped_column(BigInteger, default=0)

    payment: Mapped["Payment"] = relationship(back_populates="receipts")
