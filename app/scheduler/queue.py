"""Signed task queue for userbot-side execution (e.g. scheduled messages)."""

from __future__ import annotations

import json
import time
from typing import Any

import redis.asyncio as aioredis

from app.core.security import CommandSigner

TASK_QUEUE = "tasks:userbots"


class TaskQueue:
    def __init__(self, redis: aioredis.Redis, signer: CommandSigner) -> None:
        self.redis = redis
        self.signer = signer

    async def enqueue(self, task_id: int, user_id: int, type_: str, payload: dict) -> None:
        body: dict[str, Any] = {
            "task_id": task_id,
            "user_id": user_id,
            "type": type_,
            "payload": payload,
            "ts": int(time.time()),
        }
        body["signature"] = self.signer.sign(self._canonical(body))
        await self.redis.rpush(TASK_QUEUE, json.dumps(body, ensure_ascii=False, default=str))

    async def pop(self) -> dict[str, Any] | None:
        raw = await self.redis.lpop(TASK_QUEUE)
        if raw is None:
            return None
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            return None
        signature = body.pop("signature", None)
        if not signature or not self.signer.verify(self._canonical(body), signature):
            return None
        return body

    @staticmethod
    def _canonical(body: dict[str, Any]) -> str:
        return json.dumps(
            {
                "task_id": body.get("task_id"),
                "user_id": body.get("user_id"),
                "type": body.get("type"),
                "payload": body.get("payload"),
                "ts": body.get("ts"),
            },
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        )
