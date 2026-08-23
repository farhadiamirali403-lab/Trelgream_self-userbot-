"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis import get_redis
from app.database.session import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict:
    settings = get_settings()
    status = "ok"

    try:
        await session.execute(text("SELECT 1"))
        database = "ok"
    except Exception:  # noqa: BLE001
        database = "error"
        status = "degraded"

    try:
        redis = get_redis()
        redis_status = "ok" if await redis.ping() else "error"
    except Exception:  # noqa: BLE001
        redis_status = "error"
        status = "degraded"

    telegram = "ok" if (settings.telegram_api_id and settings.telegram_api_hash) else "not_configured"

    try:
        from sqlalchemy import select, func
        from app.database.models.workers import Worker

        worker_count = await session.scalar(select(func.count()).select_from(Worker))
        workers = "ok" if worker_count and worker_count > 0 else "no_workers"
    except Exception:  # noqa: BLE001
        workers = "error"

    return {
        "status": status,
        "database": database,
        "redis": redis_status,
        "telegram": telegram,
        "workers": workers,
    }
