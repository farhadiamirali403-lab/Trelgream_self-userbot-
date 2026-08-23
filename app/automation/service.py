"""Automation engine service: evaluate rules and dispatch actions."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.automation.actions import execute_actions
from app.automation.conditions import evaluate_all
from app.automation.repository import AutomationRuleRepository
from app.core.logging import get_logger

log = get_logger("automation")


def build_context(event) -> dict:
    """Extract a normalized dict context from a Telethon event."""
    msg = event.message
    text = getattr(msg, "message", None) or ""
    media = getattr(msg, "media", None)
    media_type = None
    if media is not None:
        media_type = media.__class__.__name__.replace("MessageMedia", "").lower()
    return {
        "text": text,
        "chat_id": getattr(event, "chat_id", None),
        "sender_id": getattr(event, "sender_id", None),
        "is_private": getattr(event, "is_private", False),
        "media_type": media_type,
        "user_joined": getattr(event, "user_joined", False),
    }


class AutomationService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = AutomationRuleRepository(session)

    async def handle_event(self, user_id: int, trigger_type: str, client, event) -> int:
        """Run all matching rules for an event; returns number of executed rules."""
        rules = await self.repo.list_enabled_for(user_id, trigger_type)
        context = build_context(event)
        executed = 0
        for rule in rules:
            if not evaluate_all(rule.conditions, context):
                continue
            await execute_actions(client, event, rule.actions)
            executed += 1
        return executed
