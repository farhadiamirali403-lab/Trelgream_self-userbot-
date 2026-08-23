"""System tools: health check."""

from __future__ import annotations

import time

from app.modules.base import BaseModule, ModuleMetadata, handler


class SysHealthModule(BaseModule):
    metadata = ModuleMetadata(
        key="sys_health", name="سلامت سلف", category="system",
        description="وضعیت سلامت سلف با /health",
    )

    def __init__(self, context) -> None:
        super().__init__(context)
        self._started = time.time()

    @handler("new_message", pattern=r"^/health")
    async def on_health(self, event) -> None:
        uptime = int(time.time() - self._started)
        hours, rem = divmod(uptime, 3600)
        minutes, seconds = divmod(rem, 60)
        try:
            me = await self.context.client.get_me()
            name = getattr(me, "first_name", "—")
        except Exception:  # noqa: BLE001
            name = "—"
        await event.reply(
            "🩺 سلامت سلف\n\n"
            f"👤 حساب: {name}\n"
            "🟢 وضعیت: آنلاین\n"
            f"⏱ آپ‌تایم: {hours}h {minutes}m {seconds}s"
        )
