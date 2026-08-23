"""Redis helpers: client factory, rate limiter, temporary auth-state store."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import get_settings
from app.core.exceptions import RateLimitError


def get_redis() -> aioredis.Redis:
    """Return a shared Redis client (connection is lazy).

    ``protocol=2`` keeps compatibility with the Redis 5.x Windows port
    (no RESP3 ``HELLO`` handshake).
    """
    return aioredis.from_url(get_settings().redis_url, decode_responses=True, protocol=2)


class RateLimiter:
    """Fixed-window rate limiter backed by Redis."""

    def __init__(self, redis: aioredis.Redis) -> None:
        self.redis = redis

    async def check(self, key: str, limit: int, window_seconds: int) -> None:
        """Raise RateLimitError if the key exceeded its limit in the window."""
        full_key = f"ratelimit:{key}"
        current = await self.redis.incr(full_key)
        if current == 1:
            await self.redis.expire(full_key, window_seconds)
        if current > limit:
            raise RateLimitError()


class AuthStateStore:
    """Temporary Telegram auth state (encrypted) with TTL in Redis."""

    def __init__(self, redis: aioredis.Redis, encrypt, decrypt) -> None:
        self.redis = redis
        self.encrypt = encrypt
        self.decrypt = decrypt
        self.ttl = 15 * 60  # 15 minutes

    def _key(self, phone: str) -> str:
        return f"auth_state:{phone}"

    async def save(self, phone: str, state: dict[str, Any]) -> None:
        payload = json.dumps(state, ensure_ascii=False)
        await self.redis.set(self._key(phone), self.encrypt(payload), ex=self.ttl)

    async def load(self, phone: str) -> dict[str, Any]:
        raw = await self.redis.get(self._key(phone))
        if raw is None:
            raise RateLimitError("وضعیت احراز هویت منقضی شده است؛ دوباره شروع کنید")
        return json.loads(self.decrypt(raw))

    async def delete(self, phone: str) -> None:
        await self.redis.delete(self._key(phone))
