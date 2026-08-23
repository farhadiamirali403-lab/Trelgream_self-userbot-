"""Public plans endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.repositories import PlanRepository
from app.database.session import get_session

router = APIRouter(prefix="/api/plans", tags=["plans"])


@router.get("")
async def list_plans(session: AsyncSession = Depends(get_session)) -> list[dict]:
    plans = await PlanRepository(session).list_active()
    return [
        {
            "id": p.id,
            "key": p.key,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "duration_days": p.duration_days,
            "max_userbots": p.max_userbots,
            "max_modules": p.max_modules,
        }
        for p in plans
    ]
