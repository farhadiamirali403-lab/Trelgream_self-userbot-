"""Billing service tests (in-memory SQLite)."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.billing.service import BillingService
from app.core.exceptions import ConflictError
from app.database.models.billing import Plan, Subscription
from app.database.models.users import User


async def _plan(session) -> Plan:
    plan = Plan(key="pro", name="Pro", price=500_000, duration_days=30, max_modules=50, sort_order=1)
    session.add(plan)
    await session.flush()
    return plan


async def _user(session, tg: int = 123) -> User:
    user = User(telegram_id=tg)
    session.add(user)
    await session.flush()
    return user


async def test_purchase_creates_pending_payment(db_session):
    plan = await _plan(db_session)
    user = await _user(db_session)
    payment = await BillingService(db_session).purchase(user.id, plan.id)
    assert payment.status == "pending"
    assert payment.reference.startswith("PAY-")


async def test_approve_activates_subscription(db_session):
    plan = await _plan(db_session)
    user = await _user(db_session)
    payment = await BillingService(db_session).purchase(user.id, plan.id)
    approved = await BillingService(db_session).approve_payment(
        payment.id, admin_id=1, admin_role="ADMIN"
    )
    assert approved.status == "approved"
    sub = (
        await db_session.execute(select(Subscription).where(Subscription.user_id == user.id))
    ).scalar_one()
    assert sub.status == "active"
    assert sub.expires_at is not None


async def test_reject_cancels_pending_subscription(db_session):
    plan = await _plan(db_session)
    user = await _user(db_session)
    payment = await BillingService(db_session).purchase(user.id, plan.id)
    rejected = await BillingService(db_session).reject_payment(
        payment.id, admin_id=1, admin_role="ADMIN"
    )
    assert rejected.status == "rejected"
    sub = (
        await db_session.execute(select(Subscription).where(Subscription.user_id == user.id))
    ).scalar_one()
    assert sub.status == "cancelled"


async def test_duplicate_active_subscription_rejected(db_session):
    plan = await _plan(db_session)
    user = await _user(db_session)
    payment = await BillingService(db_session).purchase(user.id, plan.id)
    await BillingService(db_session).approve_payment(payment.id, admin_id=1, admin_role="ADMIN")
    with pytest.raises(ConflictError):
        await BillingService(db_session).purchase(user.id, plan.id)


async def test_expire_due_subscriptions(db_session):
    from datetime import datetime, timedelta, timezone

    plan = await _plan(db_session)
    user = await _user(db_session)
    payment = await BillingService(db_session).purchase(user.id, plan.id)
    await BillingService(db_session).approve_payment(payment.id, admin_id=1, admin_role="ADMIN")

    sub = (
        await db_session.execute(select(Subscription).where(Subscription.user_id == user.id))
    ).scalar_one()
    sub.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    await db_session.flush()

    expired = await BillingService(db_session).expire_due_subscriptions()
    assert expired == 1
    await db_session.refresh(sub)
    assert sub.status == "expired"
