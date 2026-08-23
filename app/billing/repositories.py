"""Billing repositories."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.billing import Payment, PaymentReceipt, Plan, Subscription
from app.database.repository import BaseRepository


class PlanRepository(BaseRepository[Plan]):
    model = Plan

    async def get_by_key(self, key: str) -> Plan | None:
        stmt = select(Plan).where(Plan.key == key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Plan]:
        stmt = select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.sort_order, Plan.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class SubscriptionRepository(BaseRepository[Subscription]):
    model = Subscription

    async def active_for_user(self, user_id: int) -> Subscription | None:
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == user_id, Subscription.status == "active")
            .order_by(Subscription.id.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_expired_active(self, now) -> list[Subscription]:
        stmt = select(Subscription).where(
            Subscription.status == "active",
            Subscription.expires_at.is_not(None),
            Subscription.expires_at < now,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class PaymentRepository(BaseRepository[Payment]):
    model = Payment

    async def get_by_reference(self, reference: str) -> Payment | None:
        stmt = select(Payment).where(Payment.reference == reference)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_pending(self, *, limit: int = 100) -> list[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.status == "pending")
            .order_by(Payment.id.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class PaymentReceiptRepository(BaseRepository[PaymentReceipt]):
    model = PaymentReceipt
