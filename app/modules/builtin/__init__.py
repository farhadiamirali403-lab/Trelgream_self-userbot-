"""Built-in modules. Importing this package registers them in the registry."""

from app.modules.base import BaseModule, ModuleMetadata
from app.modules.builtin.anti_link import AntiLinkModule
from app.modules.builtin.auto_reply import AutoReplyModule
from app.modules.builtin.catalog import CATALOG
from app.modules.builtin.keyword_reply import KeywordReplyModule
from app.modules.builtin.welcome import WelcomeModule
from app.modules.registry import registry

# Real (implemented) modules.
registry.discover(
    AutoReplyModule,
    KeywordReplyModule,
    WelcomeModule,
    AntiLinkModule,
)

# Declared features (129-feature catalog). Unimplemented ones are registered
# with not_implemented=True so they show in the panel as "NOT IMPLEMENTED".
for _entry in CATALOG:
    _cls = type(
        f"Declared_{_entry['key']}",
        (BaseModule,),
        {"metadata": ModuleMetadata(not_implemented=True, **_entry)},
    )
    registry.register(_cls)

__all__ = [
    "AutoReplyModule",
    "KeywordReplyModule",
    "WelcomeModule",
    "AntiLinkModule",
    "CATALOG",
]
