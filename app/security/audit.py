"""Audit logging helper — every sensitive operation must be recorded."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.audit import AuditLog


async def record_audit(
    session: AsyncSession,
    *,
    actor_id: int | None,
    actor_role: str | None,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    result: str = "SUCCESS",
    metadata: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        ts=datetime.now(timezone.utc),
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        target_type=target_type,
        target_id=target_id,
        result=result,
        meta=metadata,
    )
    session.add(entry)
    await session.flush()
    return entry
