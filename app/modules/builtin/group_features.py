"""Group protection features: anti-spam, anti-flood, word filter, goodbye, filters."""

from __future__ import annotations

import time

from app.modules.base import BaseModule, ModuleMetadata, handler


class AntiSpamModule(BaseModule):
    metadata = ModuleMetadata(
        key="anti_spam", name="ضد اسپم", category="groups",
        description="حذف پیام‌های اسپم بر اساس کلمات",
        settings_schema={"words": {"label": "کلمات اسپم (با | جدا)", "type": "text", "default": "شرط بندی|کسب درآمد|قمار"}},
    )

    @handler("new_message")
    async def on_message(self, event) -> None:
        if event.is_private:
            return
        words = [w.strip() for w in str(self.setting("words", "")).split("|") if w.strip()]
        text = (event.message.message or "").lower()
        if any(w in text for w in words):
            try:
                await event.delete()
            except Exception:  # noqa: BLE001
                pass


class AntiFloodModule(BaseModule):
    metadata = ModuleMetadata(
        key="anti_flood", name="ضد سیل", category="groups",
        description="حذف پیام‌های پشت‌سرهم کاربر",
        settings_schema={"seconds": {"label": "فاصله مجاز (ثانیه)", "type": "text", "default": "2"}},
    )

    def __init__(self, context) -> None:
        super().__init__(context)
        self._last: dict = {}

    @handler("new_message")
    async def on_message(self, event) -> None:
        if event.is_private:
            return
        try:
            seconds = float(self.setting("seconds", "2"))
        except ValueError:
            seconds = 2.0
        now = time.time()
        uid = event.sender_id
        if uid in self._last and (now - self._last[uid]) < seconds:
            try:
                await event.delete()
            except Exception:  # noqa: BLE001
                pass
        self._last[uid] = now


class WordFilterModule(BaseModule):
    metadata = ModuleMetadata(
        key="word_filter", name="فیلتر کلمه", category="groups",
        description="حذف پیام‌های دارای کلمات ممنوعه",
        settings_schema={"words": {"label": "کلمات ممنوعه (با | جدا)", "type": "text", "default": ""}},
    )

    @handler("new_message")
    async def on_message(self, event) -> None:
        words = [w.strip() for w in str(self.setting("words", "")).split("|") if w.strip()]
        if not words:
            return
        text = (event.message.message or "")
        if any(w in text for w in words):
            try:
                await event.delete()
            except Exception:  # noqa: BLE001
                pass


class GoodbyeModule(BaseModule):
    metadata = ModuleMetadata(
        key="goodbye", name="خداحافظی", category="groups",
        description="پیام خداحافظی هنگام خروج عضو",
        settings_schema={"text": {"label": "متن خداحافظی", "type": "text", "default": "خداحافظ 👋"}},
    )

    @handler("new_message")
    async def on_message(self, event) -> None:
        if not getattr(event, "user_left", False):
            return
        template = str(self.setting("text", "خداحافظ 👋"))
        name = getattr(event.user, "first_name", "") if event.user else ""
        try:
            await event.respond(f"{template} {name}".strip())
        except Exception:  # noqa: BLE001
            pass


class MediaFilterModule(BaseModule):
    metadata = ModuleMetadata(
        key="media_filter", name="فیلتر رسانه", category="groups",
        description="حذف پیام‌های رسانه‌ای (عکس/ویدیو/فایل)",
    )

    @handler("new_message")
    async def on_message(self, event) -> None:
        if event.is_private:
            return
        if event.message.media is not None:
            try:
                await event.delete()
            except Exception:  # noqa: BLE001
                pass


class LinkFilterModule(BaseModule):
    metadata = ModuleMetadata(
        key="link_filter", name="فیلتر لینک", category="groups",
        description="حذف پیام‌های دارای لینک",
    )

    @handler("new_message")
    async def on_message(self, event) -> None:
        import re

        if event.is_private:
            return
        if re.search(r"https?://|t\.me/", event.message.message or ""):
            try:
                await event.delete()
            except Exception:  # noqa: BLE001
                pass


class AntiFakeModule(BaseModule):
    metadata = ModuleMetadata(
        key="anti_fake", name="ضد اکانت فیک", category="groups",
        description="حذف پیام کاربران بدون یوزرنیم (اکانت مشکوک)",
    )

    @handler("new_message")
    async def on_message(self, event) -> None:
        if event.is_private:
            return
        sender = event.sender
        username = getattr(sender, "username", None) if sender else None
        if not username:
            try:
                await event.delete()
            except Exception:  # noqa: BLE001
                pass
