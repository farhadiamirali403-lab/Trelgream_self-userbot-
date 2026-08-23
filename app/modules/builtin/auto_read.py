"""Auto read module: mark incoming messages as read."""

from __future__ import annotations

from app.modules.base import BaseModule, ModuleMetadata, handler


class AutoReadModule(BaseModule):
    metadata = ModuleMetadata(
        key="auto_read",
        name="خواندن خودکار",
        category="message",
        description="خواندن خودکار پیام‌ها (ارسال تیک خواندن)",
        permission="module.auto_read.use",
    )

    @handler("new_message")
    async def on_message(self, event) -> None:
        try:
            await self.context.client.send_read_acknowledge(event.chat_id)
        except Exception:  # noqa: BLE001
            pass
