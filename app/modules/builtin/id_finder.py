"""ID finder module: show chat/user IDs via /id."""

from __future__ import annotations

from app.modules.base import BaseModule, ModuleMetadata, handler


class IdFinderModule(BaseModule):
    metadata = ModuleMetadata(
        key="id_finder",
        name="یافتن ID",
        category="search",
        description="نمایش شناسه چت و کاربر با دستور /id",
        permission="module.id_finder.use",
    )

    @handler("new_message", pattern=r"^/id")
    async def on_id(self, event) -> None:
        text = f"🆔 چت: {event.chat_id}\n👤 کاربر: {event.sender_id}"
        try:
            chat = await event.get_chat()
            if getattr(chat, "title", None):
                text += f"\n📝 عنوان: {chat.title}"
            if getattr(chat, "username", None):
                text += f"\n🔗 @{chat.username}"
        except Exception:  # noqa: BLE001
            pass
        await event.reply(text)
