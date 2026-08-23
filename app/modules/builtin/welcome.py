"""Group welcome module."""

from __future__ import annotations

from app.modules.base import BaseModule, ModuleMetadata, handler


class WelcomeModule(BaseModule):
    metadata = ModuleMetadata(
        key="welcome",
        name="خوش‌آمدگویی",
        category="groups",
        description="خوش‌آمدگویی به اعضای جدید گروه",
        permission="module.welcome.use",
        default_enabled=False,
        settings_schema={
            "welcome_text": {"label": "متن خوش‌آمد", "type": "text", "default": "خوش آمدید 👋"},
        },
    )

    @handler("new_message")
    async def on_message(self, event) -> None:
        if not getattr(event, "user_joined", False):
            return
        template = self.setting("welcome_text", "خوش آمدید 👋")
        name = ""
        if event.user:
            name = getattr(event.user, "first_name", "") or ""
        await event.reply(f"{template} {name}".strip())
