"""Built-in modules. Importing this package registers them in the registry."""

from app.modules.builtin.anti_link import AntiLinkModule
from app.modules.builtin.auto_reply import AutoReplyModule
from app.modules.builtin.keyword_reply import KeywordReplyModule
from app.modules.builtin.welcome import WelcomeModule
from app.modules.registry import registry

registry.discover(
    AutoReplyModule,
    KeywordReplyModule,
    WelcomeModule,
    AntiLinkModule,
)

__all__ = [
    "AutoReplyModule",
    "KeywordReplyModule",
    "WelcomeModule",
    "AntiLinkModule",
]
