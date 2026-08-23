"""Keyword reply module (exact keyword -> reply text)."""

from __future__ import annotations

from app.modules.base import BaseModule, ModuleMetadata, handler


class KeywordReplyModule(BaseModule):
    metadata = ModuleMetadata(
        key="keyword_reply",
        name="پاسخ کلیدواژه",
        category="message",
        description="پاسخ خودکار بر اساس کلیدواژه‌ها",
        permission="module.keyword_reply.use",
        default_enabled=False,
    )

    @handler("new_message")
    async def on_message(self, event) -> None:
        text = (event.message.message or "").strip()
        if not text:
            return
        # settings: {"keywords": {"سلام": "سلام 👋", "قیمت": "..."}}
        keywords: dict = self.setting("keywords", {})
        reply = keywords.get(text)
        if reply:
            await event.reply(reply)
