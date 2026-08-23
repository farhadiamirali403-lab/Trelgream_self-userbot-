"""Per-userbot runtime: Telethon client + enabled modules."""

from __future__ import annotations

from telethon import TelegramClient, events

from app.core.exceptions import SessionError
from app.modules.base import BaseModule, ModuleContext
from app.modules.registry import ModuleRegistry

_EVENT_BUILDERS = {
    "new_message": events.NewMessage,
    "edited_message": events.MessageEdited,
    "deleted_message": events.MessageDeleted,
}


class UserbotRuntime:
    """Owns a single userbot's client and module instances."""

    def __init__(
        self,
        *,
        user_id: int,
        userbot_id: int,
        client: TelegramClient,
        registry: ModuleRegistry,
        module_classes: list[type[BaseModule]],
        module_settings: dict[str, dict],
    ) -> None:
        self.user_id = user_id
        self.userbot_id = userbot_id
        self.client = client
        self.registry = registry
        self.module_classes = module_classes
        self.module_settings = module_settings
        self.modules: list[BaseModule] = []

    async def start(self) -> None:
        await self.client.connect()
        if not await self.client.is_user_authorized():
            raise SessionError("نشست تلگرام نامعتبر است")
        for module_cls in self.module_classes:
            ctx = ModuleContext(
                user_id=self.user_id,
                userbot_id=self.userbot_id,
                client=self.client,
                settings=self.module_settings.get(module_cls.metadata.key, {}),
            )
            module = module_cls(ctx)
            self.modules.append(module)
            for spec in module_cls.handlers():
                builder = _EVENT_BUILDERS.get(spec.event_type)
                if builder is None:
                    continue
                kwargs: dict = {"incoming": spec.incoming, "outgoing": spec.outgoing}
                if spec.pattern:
                    kwargs["pattern"] = spec.pattern
                self.client.add_event_handler(spec.func.__get__(module), builder(**kwargs))
        for module in self.modules:
            await module.on_start()

    async def stop(self) -> None:
        for module in self.modules:
            await module.on_stop()
        await self.client.disconnect()
