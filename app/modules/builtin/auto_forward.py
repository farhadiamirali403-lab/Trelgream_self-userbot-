"""Auto forward module: forward messages from a source chat to a target."""

from __future__ import annotations

from app.modules.base import BaseModule, ModuleMetadata, handler


class AutoForwardModule(BaseModule):
    metadata = ModuleMetadata(
        key="auto_forward",
        name="فوروارد خودکار",
        category="channels",
        description="فوروارد خودکار پیام‌ها از یک چت به چت دیگر",
        permission="module.auto_forward.use",
        settings_schema={
            "source": {"label": "چت مبدأ (یوزرنیم یا ID)", "type": "text", "default": ""},
            "target": {"label": "چت مقصد (یوزرنیم یا ID)", "type": "text", "default": ""},
        },
    )

    @handler("new_message")
    async def on_message(self, event) -> None:
        source = str(self.setting("source", "")).strip()
        target = str(self.setting("target", "")).strip()
        if not source or not target:
            return
        try:
            chat = await event.get_chat()
        except Exception:  # noqa: BLE001
            return
        cid = str(getattr(chat, "id", ""))
        cname = getattr(chat, "username", None) or ""
        if cid == source or cname == source.lstrip("@"):
            await self.context.client.forward_messages(target, event.message)
