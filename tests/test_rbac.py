"""RBAC seeding and permission resolution tests."""

from __future__ import annotations

from sqlalchemy import select

from app.auth.permissions import ALL_PERMISSIONS
from app.auth.rbac import get_admin_permissions
from app.database.models.admins import Admin, AdminRole, Role
from app.database.seed import seed_rbac


async def test_owner_has_all_permissions(db_session):
    await seed_rbac(db_session)

    admin = Admin(telegram_id="999")
    db_session.add(admin)
    await db_session.flush()

    owner_role = (await db_session.execute(select(Role).where(Role.name == "OWNER"))).scalar_one()
    db_session.add(AdminRole(admin_id=admin.id, role_id=owner_role.id))
    await db_session.flush()

    perms = await get_admin_permissions(db_session, admin.id)
    assert set(perms) == set(ALL_PERMISSIONS)


async def test_support_has_limited_permissions(db_session):
    await seed_rbac(db_session)

    admin = Admin(telegram_id="888")
    db_session.add(admin)
    await db_session.flush()

    support_role = (
        await db_session.execute(select(Role).where(Role.name == "SUPPORT"))
    ).scalar_one()
    db_session.add(AdminRole(admin_id=admin.id, role_id=support_role.id))
    await db_session.flush()

    perms = await get_admin_permissions(db_session, admin.id)
    assert "support.manage" in perms
    assert "users.suspend" not in perms
    assert "payments.approve" not in perms
