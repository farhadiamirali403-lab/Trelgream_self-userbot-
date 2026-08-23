"""Message tools: auto delete, auto typing, message logger."""

from __future__ import annotations

import asyncio

from app.modules.base import BaseModule, ModuleMetadata, handler


class AutoDeleteModule(BaseModule):
    metadata = ModuleMetadata(
        key="auto_delete", name="حذف خودکار", category="message",
        description="حذف خودکار پیام‌های ارسالی پس از چند ثانیه",
        settings_schema={
            "delay": {"label": "تاخیر (ثانیه)", "type": "text", "default": "30"},
        },
    )

    @handler("new_message", outgoing=True)
    async def on_outgoing(self, event) -> None:
        try:
            delay = int(self.setting("delay", "30"))
        except ValueError:
            delay = 30
        await asyncio.sleep(delay)
        try:
            await event.delete()
        except Exception:  # noqa: BLE001
            pass


class AutoTypingModule(BaseModule):
    metadata = ModuleMetadata(
        key="auto_typing", name="تایپ خودکار", category="message",
        description="نمایش وضعیت تایپ خودکار هنگام دریافت پیام",
        settings_schema={
            "duration": {"label": "مدت (ثانیه)", "type": "text", "default": "5"},
        },
    )

    @handler("new_message")
    async def on_message(self, event) -> None:
        try:
            duration = int(self.setting("duration", "5"))
        except ValueError:
            duration = 5
        try:
            async with self.context.client.action(event.chat_id, "typing"):
                await asyncio.sleep(min(duration, 20))
        except Exception:  # noqa: BLE001
            pass


class MessageLoggerModule(BaseModule):
    metadata = ModuleMetadata(
        key="message_logger", name="ثبت پیام", category="message",
        description="فوروارد خودکار پیام‌ها به یک چت (برای ثبت)",
        settings_schema={
            "target": {"label": "چت مقصد (یوزرنیم یا ID)", "type": "text", "default": "me"},
        },
    )

    @handler("new_message")
    async def on_message(self, event) -> None:
        target = str(self.setting("target", "me")).strip()
        if not target:
            return
        try:
            await self.context.client.forward_messages(target, event.message)
        except Exception:  # noqa: BLE001
            pass
