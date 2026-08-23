"""Automation rule repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.automation import AutomationRule
from app.database.repository import BaseRepository


class AutomationRuleRepository(BaseRepository[AutomationRule]):
    model = AutomationRule

    async def list_enabled_for(self, user_id: int, trigger_type: str) -> list[AutomationRule]:
        stmt = (
            select(AutomationRule)
            .options(
                selectinload(AutomationRule.conditions),
                selectinload(AutomationRule.actions),
            )
            .where(
                AutomationRule.user_id == user_id,
                AutomationRule.enabled.is_(True),
                AutomationRule.trigger_type == trigger_type,
            )
            .order_by(AutomationRule.priority, AutomationRule.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())
