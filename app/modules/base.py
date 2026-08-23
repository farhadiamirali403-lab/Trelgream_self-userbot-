"""Module (plugin) base class and handler decorator.

Each feature is a CORE / MODULE / PLUGIN. Core stays small; modules are
discovered by the registry, enabled per-user, gated by permission and
subscription plan limits, and receive a per-userbot runtime context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class ModuleMetadata:
    key: str
    name: str
    category: str = "general"
    version: str = "1.0.0"
    description: str = ""
    # Permission required to use this module (e.g. "module.auto_reply.use").
    permission: str | None = None
    default_enabled: bool = False
    is_core: bool = False


@dataclass
class HandlerSpec:
    func: Callable
    event_type: str = "new_message"
    pattern: str | None = None
    incoming: bool = True
    outgoing: bool = False


@dataclass
class ModuleContext:
    """Runtime context handed to each module instance."""

    user_id: int
    userbot_id: int
    client: Any  # Telethon TelegramClient
    settings: dict[str, Any] = field(default_factory=dict)


def handler(
    event_type: str = "new_message",
    *,
    pattern: str | None = None,
    incoming: bool = True,
    outgoing: bool = False,
) -> Callable:
    """Decorator that registers a method as a module event handler."""

    def deco(func: Callable) -> Callable:
        setattr(
            func,
            "_module_handler",
            HandlerSpec(
                func=func,
                event_type=event_type,
                pattern=pattern,
                incoming=incoming,
                outgoing=outgoing,
            ),
        )
        return func

    return deco


class BaseModule:
    """Base class for all modules. Subclass and add @handler methods."""

    metadata: ModuleMetadata = ModuleMetadata(key="base", name="Base")

    def __init__(self, context: ModuleContext) -> None:
        self.context = context

    # --- lifecycle ---

    async def on_start(self) -> None:
        """Called when the module is enabled for a userbot."""

    async def on_stop(self) -> None:
        """Called when the module is disabled or the userbot stops."""

    # --- handler discovery ---

    @classmethod
    def handlers(cls) -> list[HandlerSpec]:
        specs: list[HandlerSpec] = []
        for name in dir(cls):
            attr = getattr(cls, name)
            spec = getattr(attr, "_module_handler", None)
            if isinstance(spec, HandlerSpec):
                specs.append(spec)
        return specs

    # --- helpers ---

    async def reply(self, event: Any, text: str) -> None:
        await event.reply(text)

    def setting(self, key: str, default: Any = None) -> Any:
        return self.context.settings.get(key, default)
