"""Billing service: plans, subscriptions, card payments, approval workflow."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.repositories import (
    PaymentReceiptRepository,
    PaymentRepository,
    PlanRepository,
    SubscriptionRepository,
)
from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.database.models.billing import Payment, PaymentReceipt, Plan, Subscription
from app.database.models.userbots import Userbot
from app.security.audit import record_audit


def _now() -> datetime:
    return datetime.now(timezone.utc)


class BillingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.plans = PlanRepository(session)
        self.subscriptions = SubscriptionRepository(session)
        self.payments = PaymentRepository(session)
        self.receipts = PaymentReceiptRepository(session)

    # --- plans ---

    async def list_plans(self) -> list[Plan]:
        return await self.plans.list_active()

    async def get_plan(self, plan_id: int) -> Plan:
        return await self.plans.get_or_raise(plan_id)

    # --- subscription / payment creation ---

    async def purchase(self, user_id: int, plan_id: int) -> Payment:
        plan = await self.plans.get_or_raise(plan_id)
        if not plan.is_active:
            raise ConflictError("این پلن غیرفعال است")

        active = await self.subscriptions.active_for_user(user_id)
        if active is not None:
            raise ConflictError("شما اشتراک فعال دارید")

        subscription = Subscription(
            user_id=user_id, plan_id=plan.id, status="pending"
        )
        self.session.add(subscription)
        await self.session.flush()

        payment = Payment(
            user_id=user_id,
            plan_id=plan.id,
            subscription_id=subscription.id,
            amount=plan.price,
            status="pending",
            method="card",
            reference="PENDING",  # placeholder; replaced after id is assigned
        )
        payment = await self.payments.add(payment)
        payment.reference = f"PAY-{payment.id:06d}"
        await self.session.flush()
        return payment

    async def add_receipt(
        self,
        payment_id: int,
        *,
        storage_key: str,
        file_name: str | None,
        mime_type: str | None,
        size: int,
    ) -> PaymentReceipt:
        payment = await self.payments.get_or_raise(payment_id)
        if payment.status != "pending":
            raise ConflictError("این پرداخت در وضعیت بررسی نیست")
        receipt = PaymentReceipt(
            payment_id=payment.id,
            storage_key=storage_key,
            file_name=file_name,
            mime_type=mime_type,
            size=size,
        )
        return await self.receipts.add(receipt)

    # --- approval ---

    async def approve_payment(
        self, payment_id: int, *, admin_id: int, admin_role: str
    ) -> Payment:
        payment = await self.payments.get_or_raise(payment_id)
        if payment.status != "pending":
            raise ConflictError("این پرداخت قبلاً بررسی شده است")

        plan = await self.plans.get_or_raise(payment.plan_id)
        now = _now()
        payment.status = "approved"
        payment.reviewed_by = admin_id
        payment.reviewed_at = now

        subscription = await self.subscriptions.get_or_raise(payment.subscription_id)
        subscription.plan_id = plan.id
        subscription.status = "active"
        subscription.started_at = now
        subscription.expires_at = now + timedelta(days=plan.duration_days)

        # Resume a previously suspended userbot (if any).
        await self._set_userbot_status(subscription.user_id, "STOPPED")

        await record_audit(
            self.session,
            actor_id=admin_id,
            actor_role=admin_role,
            action="APPROVE_PAYMENT",
            target_type="PAYMENT",
            target_id=payment.reference,
            result="SUCCESS",
        )
        await self.session.flush()
        return payment

    async def reject_payment(
        self, payment_id: int, *, admin_id: int, admin_role: str, reason: str | None = None
    ) -> Payment:
        payment = await self.payments.get_or_raise(payment_id)
        if payment.status != "pending":
            raise ConflictError("این پرداخت قبلاً بررسی شده است")

        payment.status = "rejected"
        payment.reviewed_by = admin_id
        payment.reviewed_at = _now()
        payment.reject_reason = reason

        if payment.subscription_id is not None:
            sub = await self.subscriptions.get(payment.subscription_id)
            if sub is not None and sub.status == "pending":
                sub.status = "cancelled"

        await record_audit(
            self.session,
            actor_id=admin_id,
            actor_role=admin_role,
            action="REJECT_PAYMENT",
            target_type="PAYMENT",
            target_id=payment.reference,
            result="SUCCESS",
        )
        await self.session.flush()
        return payment

    # --- expiration (scheduler) ---

    async def expire_due_subscriptions(self) -> int:
        """Mark past-due active subscriptions expired and suspend their userbots."""
        due = await self.subscriptions.list_expired_active(_now())
        for sub in due:
            sub.status = "expired"
            await self._set_userbot_status(sub.user_id, "SUSPENDED")
        await self.session.flush()
        return len(due)

    async def _set_userbot_status(self, user_id: int, status: str) -> None:
        from sqlalchemy import select, update

        stmt = (
            update(Userbot)
            .where(Userbot.user_id == user_id, Userbot.status != status)
            .values(status=status)
        )
        await self.session.execute(stmt)

    # --- query helpers for admin ---

    async def pending_payments(self, *, limit: int = 100) -> list[Payment]:
        return await self.payments.list_pending(limit=limit)
