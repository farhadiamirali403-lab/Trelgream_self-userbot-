"""Signed internal command bus (Redis list) with replay/forgery protection.

Every command carries: command_id, timestamp, actor, target, expiration and an
HMAC signature. The worker verifies signature and expiration before acting.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

import redis.asyncio as aioredis

from app.core.security import CommandSigner

COMMAND_QUEUE = "commands:userbots"
COMMAND_TTL = 300  # seconds


class CommandBus:
    def __init__(self, redis: aioredis.Redis, signer: CommandSigner) -> None:
        self.redis = redis
        self.signer = signer

    async def send(
        self, action: str, target_id: int, *, actor_id: int | None, actor_role: str | None
    ) -> str:
        """Enqueue a signed command; returns its command_id."""
        command_id = uuid.uuid4().hex
        now = int(time.time())
        body: dict[str, Any] = {
            "command_id": command_id,
            "ts": now,
            "expires_at": now + COMMAND_TTL,
            "action": action,  # start / stop / restart
            "target_id": target_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
        }
        signature = self.signer.sign(self._canonical(body))
        body["signature"] = signature
        await self.redis.rpush(COMMAND_QUEUE, json.dumps(body))
        return command_id

    async def pop(self) -> dict[str, Any] | None:
        """Pop and validate one command, or None if queue is empty."""
        raw = await self.redis.lpop(COMMAND_QUEUE)
        if raw is None:
            return None
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            return None  # drop malformed
        signature = body.pop("signature", None)
        if not signature:
            return None
        if not self.signer.verify(self._canonical(body), signature):
            return None  # forged / tampered
        if body.get("expires_at", 0) < int(time.time()):
            return None  # expired
        return body

    @staticmethod
    def _canonical(body: dict[str, Any]) -> str:
        fields = ["command_id", "ts", "expires_at", "action", "target_id", "actor_id", "actor_role"]
        return "|".join(str(body.get(f, "")) for f in fields)
