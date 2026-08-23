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
        settings_schema={
            "reply_text": {"label": "متن پاسخ", "type": "text", "default": "پیام شما دریافت شد ✅"},
        },
    )

    @handler("new_message")
    async def on_message(self, event) -> None:
        msg = event.message.message or ""
        if msg.startswith("/"):
            return
        if event.is_private:
            text = self.setting("reply_text", "پیام شما دریافت شد ✅")
            await event.reply(text)

    @handler("new_message", pattern=r"^/setreply")
    async def on_setreply(self, event) -> None:
        text = (event.message.message or "")[9:].strip()
        if not text:
            await event.reply("استفاده: /setreply متن پاسخ")
            return
        await self.persist_setting("reply_text", text)
        await event.reply(f"✅ متن پاسخ خودکار تنظیم شد:\n{text}")
