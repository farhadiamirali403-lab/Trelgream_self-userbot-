"""Idempotent database seeding: plans, RBAC, modules, owner."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import ALL_PERMISSIONS, DEFAULT_ROLE_PERMISSIONS, ROLE_NAMES
from app.core.config import get_settings
from app.database.models.admins import Admin, AdminRole, Permission, Role, RolePermission
from app.database.models.billing import Plan
from app.database.models.modules import Module

PLANS = [
    {
        "key": "basic",
        "name": "پایه",
        "description": "پلن شروع برای کاربران عادی",
        "price": 200_000,
        "duration_days": 30,
        "max_userbots": 1,
        "max_modules": 10,
        "max_automation_rules": 5,
        "max_scheduled_tasks": 5,
        "sort_order": 1,
    },
    {
        "key": "pro",
        "name": "حرفه‌ای",
        "description": "برای کاربران حرفه‌ای",
        "price": 500_000,
        "duration_days": 30,
        "max_userbots": 2,
        "max_modules": 50,
        "max_automation_rules": 50,
        "max_scheduled_tasks": 50,
        "sort_order": 2,
    },
    {
        "key": "premium",
        "name": "پریمیوم",
        "description": "دسترسی کامل به تمام قابلیت‌ها",
        "price": 1_200_000,
        "duration_days": 30,
        "max_userbots": 5,
        "max_modules": 129,
        "max_automation_rules": 200,
        "max_scheduled_tasks": 200,
        "sort_order": 3,
    },
    {
        "key": "business",
        "name": "بیزینس",
        "description": "برای کسب‌وکارها و تیم‌ها",
        "price": 3_000_000,
        "duration_days": 30,
        "max_userbots": 20,
        "max_modules": 200,
        "max_automation_rules": 1000,
        "max_scheduled_tasks": 1000,
        "sort_order": 4,
    },
]


async def _exists(session: AsyncSession, model, **filters) -> bool:
    stmt = select(model)
    for k, v in filters.items():
        stmt = stmt.where(getattr(model, k) == v)
    result = await session.execute(stmt.limit(1))
    return result.first() is not None


async def seed_plans(session: AsyncSession) -> None:
    for plan in PLANS:
        if not await _exists(session, Plan, key=plan["key"]):
            session.add(Plan(**plan))
    await session.flush()


async def seed_rbac(session: AsyncSession) -> None:
    # Permissions
    for code in ALL_PERMISSIONS:
        if not await _exists(session, Permission, code=code):
            session.add(Permission(code=code))
    await session.flush()

    # Roles
    for name in ROLE_NAMES:
        if not await _exists(session, Role, name=name):
            session.add(Role(name=name))
    await session.flush()

    # Fetch roles + permissions
    roles = {r.name: r for r in (await session.execute(select(Role))).scalars().all()}
    perms = {p.code: p for p in (await session.execute(select(Permission))).scalars().all()}

    # Role -> permissions
    for role_name, role in roles.items():
        codes = ALL_PERMISSIONS if role_name == "OWNER" else DEFAULT_ROLE_PERMISSIONS.get(role_name, set())
        for code in codes:
            if not await _exists(session, RolePermission, role_id=role.id, permission_id=perms[code].id):
                session.add(RolePermission(role_id=role.id, permission_id=perms[code].id))
    await session.flush()


async def seed_modules(session: AsyncSession) -> None:
    from app.modules.builtin import registry  # populates the registry

    for meta in registry.metadata_list():
        if not await _exists(session, Module, key=meta["key"]):
            session.add(
                Module(
                    key=meta["key"],
                    name=meta["name"],
                    category=meta["category"],
                    version=meta["version"],
                    description=meta["description"],
                    is_core=meta["is_core"],
                    default_enabled=meta["default_enabled"],
                    meta={
                        "permission": meta["permission"],
                        "not_implemented": meta.get("not_implemented", False),
                    },
                )
            )
    await session.flush()


async def seed_owner(session: AsyncSession) -> None:
    settings = get_settings()
    if not settings.owner_telegram_id:
        return
    tg_id = str(settings.owner_telegram_id)
    if await _exists(session, Admin, telegram_id=tg_id):
        return
    admin = Admin(telegram_id=tg_id, name="Owner", is_active=True)
    session.add(admin)
    await session.flush()
    owner_role = (
        await session.execute(select(Role).where(Role.name == "OWNER"))
    ).scalar_one()
    session.add(AdminRole(admin_id=admin.id, role_id=owner_role.id))
    await session.flush()


async def seed_all(session: AsyncSession) -> None:
    await seed_plans(session)
    await seed_rbac(session)
    await seed_modules(session)
    await seed_owner(session)
    await session.commit()
