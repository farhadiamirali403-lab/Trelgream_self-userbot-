"""Built-in modules. Importing this package registers them in the registry."""

from app.modules.base import BaseModule, ModuleMetadata
from app.modules.builtin.anti_link import AntiLinkModule
from app.modules.builtin.auto_forward import AutoForwardModule
from app.modules.builtin.auto_message import AutoMessageModule
from app.modules.builtin.auto_read import AutoReadModule
from app.modules.builtin.auto_reply import AutoReplyModule
from app.modules.builtin.catalog import CATALOG
from app.modules.builtin.channel_features import PostTemplatesModule, ScheduledPostsModule
from app.modules.builtin.entertainment import (
    AppInfoModule,
    CalcModule,
    GifSearchModule,
    ImageSearchModule,
    MusicModule,
    TimeModule,
    WeatherModule,
    WikiModule,
)
from app.modules.builtin.extra_features import (
    AutoEditModule,
    ChatStatsModule,
    RenameModule,
    UsageReportModule,
    UserSearchModule,
)
from app.modules.builtin.group_features import (
    AntiFakeModule,
    AntiFloodModule,
    AntiSpamModule,
    GoodbyeModule,
    LinkFilterModule,
    MediaFilterModule,
    WordFilterModule,
)
from app.modules.builtin.id_finder import IdFinderModule
from app.modules.builtin.info_tools import (
    ChatSearchModule,
    GroupInfoModule,
    PersonIdModule,
    SaveToPvModule,
    SessionsModule,
    UserInfoByIdModule,
)
from app.modules.builtin.keyword_reply import KeywordReplyModule
from app.modules.builtin.message_tools import (
    AutoDeleteModule,
    AutoTypingModule,
    MessageLoggerModule,
)
from app.modules.builtin.moderation import (
    BanModule,
    KickModule,
    MuteModule,
    PurgeModule,
    UnbanModule,
    UnmuteModule,
    WarnModule,
)
from app.modules.builtin.more_info import (
    ChatInfoModule,
    DownloaderModule,
    FileInfoModule,
    LinkExtractorModule,
    MessageInfoModule,
)
from app.modules.builtin.system_tools import SysHealthModule
from app.modules.builtin.tools import (
    CurrencyModule,
    EnemyModule,
    GoldModule,
    LinkButtonModule,
)
from app.modules.builtin.user_info import UserInfoModule
from app.modules.builtin.welcome import WelcomeModule
from app.modules.registry import registry

# Real (implemented) modules.
registry.discover(
    AutoReplyModule,
    KeywordReplyModule,
    WelcomeModule,
    AntiLinkModule,
    AutoMessageModule,
    AutoForwardModule,
    AutoReadModule,
    IdFinderModule,
    UserInfoModule,
    WikiModule,
    WeatherModule,
    MusicModule,
    ImageSearchModule,
    GifSearchModule,
    CalcModule,
    TimeModule,
    AppInfoModule,
    UserInfoByIdModule,
    GroupInfoModule,
    SessionsModule,
    SaveToPvModule,
    PersonIdModule,
    ChatSearchModule,
    CurrencyModule,
    GoldModule,
    LinkButtonModule,
    EnemyModule,
    MuteModule,
    UnmuteModule,
    BanModule,
    UnbanModule,
    KickModule,
    PurgeModule,
    WarnModule,
    AutoDeleteModule,
    AutoTypingModule,
    MessageLoggerModule,
    ChatInfoModule,
    MessageInfoModule,
    LinkExtractorModule,
    FileInfoModule,
    DownloaderModule,
    SysHealthModule,
    AntiSpamModule,
    AntiFloodModule,
    WordFilterModule,
    GoodbyeModule,
    MediaFilterModule,
    LinkFilterModule,
    AntiFakeModule,
    ScheduledPostsModule,
    PostTemplatesModule,
    UserSearchModule,
    ChatStatsModule,
    UsageReportModule,
    RenameModule,
    AutoEditModule,
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
    "AutoMessageModule",
    "AutoForwardModule",
    "AutoReadModule",
    "IdFinderModule",
    "UserInfoModule",
    "CATALOG",
]
