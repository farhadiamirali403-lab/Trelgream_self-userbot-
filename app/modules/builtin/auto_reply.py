"""Auto-reply module."""

from __future__ import annotations

from app.modules.base import BaseModule, ModuleMetadata, handler


class AutoReplyModule(BaseModule):
    metadata = ModuleMetadata(
        key="auto_reply",
        name="پاسخ خودکار",
        category="message",
        description="پاسخ خودکار به پیام‌های دریافتی",
        permission="module.auto_reply.use",
        default_enabled=False,
    )

    @handler("new_message")
    async def on_message(self, event) -> None:
        if event.is_private:
            text = self.setting("reply_text", "پیام شما دریافت شد ✅")
            await event.reply(text)
