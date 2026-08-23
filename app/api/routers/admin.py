"""Admin REST endpoints (protected by X-Admin-Key)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.billing.service import BillingService
from app.database.models.users import User
from app.database.models.userbots import Userbot
from app.database.models.workers import Worker
from app.database.session import get_session
from app.users.repository import UserRepository

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/stats")
async def stats(session: AsyncSession = Depends(get_session)) -> dict:
    users = await session.scalar(select(func.count()).select_from(User))
    online = await session.scalar(
        select(func.count()).select_from(Userbot).where(Userbot.status == "RUNNING")
    )
    workers = await session.scalar(select(func.count()).select_from(Worker))
    return {"users": users, "online_userbots": online, "workers": workers}


@router.get("/users")
async def list_users(
    q: str | None = None, limit: int = 50, session: AsyncSession = Depends(get_session)
) -> list[dict]:
    users = await UserRepository(session).search(query=q, limit=limit)
    return [
        {
            "id": u.id,
            "telegram_id": u.telegram_id,
            "username": u.username,
            "phone": u.phone,
            "is_active": u.is_active,
            "is_suspended": u.is_suspended,
        }
        for u in users
    ]


@router.get("/userbots")
async def list_userbots(limit: int = 100, session: AsyncSession = Depends(get_session)) -> list[dict]:
    from app.userbots.repository import UserbotRepository

    userbots = await UserbotRepository(session).list_all(limit=limit)
    return [
        {
            "id": u.id,
            "user_id": u.user_id,
            "status": u.status,
            "worker_id": u.current_worker_id,
            "last_heartbeat": u.last_heartbeat_at,
        }
        for u in userbots
    ]


@router.get("/payments/pending")
async def pending_payments(session: AsyncSession = Depends(get_session)) -> list[dict]:
    payments = await BillingService(session).pending_payments()
    return [
        {
            "id": p.id,
            "reference": p.reference,
            "user_id": p.user_id,
            "amount": p.amount,
            "status": p.status,
        }
        for p in payments
    ]


@router.post("/payments/{payment_id}/approve")
async def approve_payment(payment_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    payment = await BillingService(session).approve_payment(
        payment_id, admin_id=0, admin_role="ADMIN"
    )
    await session.commit()
    return {"reference": payment.reference, "status": payment.status}


@router.post("/payments/{payment_id}/reject")
async def reject_payment(
    payment_id: int, reason: str | None = None, session: AsyncSession = Depends(get_session)
) -> dict:
    payment = await BillingService(session).reject_payment(
        payment_id, admin_id=0, admin_role="ADMIN", reason=reason
    )
    await session.commit()
    return {"reference": payment.reference, "status": payment.status}
