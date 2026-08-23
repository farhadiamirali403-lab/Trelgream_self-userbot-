"""Anti-link module (group moderation)."""

from __future__ import annotations

import re

from app.modules.base import BaseModule, ModuleMetadata, handler

_LINK_RE = re.compile(r"(https?://|t\.me/|telegram\.me/)", re.IGNORECASE)


class AntiLinkModule(BaseModule):
    metadata = ModuleMetadata(
        key="anti_link",
        name="ضد لینک",
        category="groups",
        description="حذف یا هشدار لینک‌های ارسالی در گروه",
        permission="module.anti_link.use",
        default_enabled=False,
        settings_schema={
            "mode": {
                "label": "حالت",
                "type": "choice",
                "choices": {"delete": "🗑 حذف لینک", "warn": "⚠️ هشدار"},
                "default": "delete",
            },
        },
    )

    @handler("new_message")
    async def on_message(self, event) -> None:
        if event.is_private:
            return
        text = event.message.message or ""
        if not _LINK_RE.search(text):
            return
        mode = self.setting("mode", "delete")  # delete | warn
        if mode == "delete":
            await event.delete()
        else:
            await event.reply("لینک مجاز نیست ⚠️")
