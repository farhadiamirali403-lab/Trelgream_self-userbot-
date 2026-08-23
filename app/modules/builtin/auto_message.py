"""Auto message module: send a message to a target on an interval."""

from __future__ import annotations

import asyncio

from app.modules.base import BaseModule, ModuleMetadata


class AutoMessageModule(BaseModule):
    metadata = ModuleMetadata(
        key="auto_message",
        name="ارسال خودکار",
        category="message",
        description="ارسال خودکار یک پیام به یک کاربر/چت با فاصله زمانی مشخص",
        permission="module.auto_message.use",
        settings_schema={
            "target": {"label": "گیرنده (یوزرنیم یا ID)", "type": "text", "default": "me"},
            "text": {"label": "متن پیام", "type": "text", "default": "سلام 👋"},
            "interval": {"label": "فاصله (ثانیه)", "type": "text", "default": "60"},
        },
    )

    def __init__(self, context) -> None:
        super().__init__(context)
        self._task: asyncio.Task | None = None
        self._stop = False

    async def on_start(self) -> None:
        self._stop = False
        self._task = asyncio.create_task(self._loop())

    async def on_stop(self) -> None:
        self._stop = True
        if self._task:
            self._task.cancel()

    async def _loop(self) -> None:
        while not self._stop:
            try:
                target = str(self.setting("target", "me")).strip()
                text = str(self.setting("text", "سلام 👋"))
                interval = int(self.setting("interval", "60"))
                if interval < 5:
                    interval = 5
                await self.context.client.send_message(target, text)
            except asyncio.CancelledError:
                break
            except Exception:  # noqa: BLE001 - keep looping
                pass
            await asyncio.sleep(interval)
