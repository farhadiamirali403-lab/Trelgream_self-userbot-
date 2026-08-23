"""Redis-backed conversation state for the central bot."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis


class ConversationState:
    def __init__(self, redis: aioredis.Redis) -> None:
        self.redis = redis

    def _key(self, tg_id: int) -> str:
        return f"bot_state:{tg_id}"

    async def set(self, tg_id: int, state: str, data: dict[str, Any] | None = None) -> None:
        await self.redis.set(
            self._key(tg_id),
            json.dumps({"state": state, "data": data or {}}, ensure_ascii=False),
            ex=15 * 60,
        )

    async def get(self, tg_id: int) -> tuple[str, dict[str, Any]] | None:
        raw = await self.redis.get(self._key(tg_id))
        if raw is None:
            return None
        obj = json.loads(raw)
        return obj.get("state"), obj.get("data", {})

    async def clear(self, tg_id: int) -> None:
        await self.redis.delete(self._key(tg_id))
