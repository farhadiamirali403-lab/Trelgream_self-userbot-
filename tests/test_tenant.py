"""Tenant isolation tests."""

from __future__ import annotations

import pytest

from app.automation.repository import AutomationRuleRepository
from app.core.exceptions import NotFoundError
from app.database.models.automation import AutomationRule
from app.database.models.users import User


async def test_tenant_isolation_prevents_cross_access(db_session):
    user_a = User(telegram_id=1)
    user_b = User(telegram_id=2)
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    rule = AutomationRule(user_id=user_a.id, name="rule-a", trigger_type="new_message")
    db_session.add(rule)
    await db_session.flush()

    repo = AutomationRuleRepository(db_session)

    # Owner can access.
    got = await repo.get_for_tenant(rule.id, user_a.id)
    assert got.id == rule.id

    # Other tenant must NOT access (raised as NotFound to avoid existence leak).
    with pytest.raises(NotFoundError):
        await repo.get_for_tenant(rule.id, user_b.id)
