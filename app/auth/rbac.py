"""RBAC service: resolve an admin's effective permission set."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.admins import Admin, AdminRole, Permission, Role, RolePermission


async def get_admin_permissions(session: AsyncSession, admin_id: int) -> set[str]:
    """Return the set of permission codes an admin holds via their roles."""
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(AdminRole, AdminRole.role_id == Role.id)
        .where(AdminRole.admin_id == admin_id)
        .distinct()
    )
    result = await session.execute(stmt)
    return {row[0] for row in result.all()}


async def admin_has_permission(session: AsyncSession, admin_id: int, permission: str) -> bool:
    """Check whether an admin has a given permission."""
    return permission in await get_admin_permissions(session, admin_id)


async def get_admin_by_telegram_id(session: AsyncSession, telegram_id: int) -> Admin | None:
    stmt = select(Admin).where(Admin.telegram_id == str(telegram_id))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
