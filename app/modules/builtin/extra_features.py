"""Search/stats/media extras: user search, chat stats, usage, rename, auto edit."""

from __future__ import annotations

import asyncio
from collections import Counter

from app.modules.base import BaseModule, ModuleMetadata, handler


class UserSearchModule(BaseModule):
    metadata = ModuleMetadata(
        key="user_search", name="جستجوی کاربر", category="search",
        description="جستجوی کاربر در چت با /usersearch نام",
    )

    @handler("new_message", pattern=r"^/usersearch")
    async def on_usearch(self, event) -> None:
        query = (event.message.message or "")[11:].strip()
        if not query:
            await event.reply("استفاده: /usersearch نام")
            return
        try:
            participants = await self.context.client.get_participants(event.chat_id, search=query, limit=10)
        except Exception:  # noqa: BLE001
            await event.reply("جستجو فقط در گروه ممکن است.")
            return
        if not participants:
            await event.reply("کاربری یافت نشد.")
            return
        lines = ["👥 نتایج جستجو:"]
        for p in participants:
            name = f"{getattr(p, 'first_name', '') or ''} {getattr(p, 'last_name', '') or ''}".strip()
            lines.append(f"• {name} — @{getattr(p, 'username', None) or '—'} (ID: {p.id})")
        await event.reply("\n".join(lines))


class ChatStatsModule(BaseModule):
    metadata = ModuleMetadata(
        key="chat_stats", name="آمار چت", category="search",
        description="آمار پیام‌های اخیر چت با /chatstats",
    )

    @handler("new_message", pattern=r"^/chatstats")
    async def on_chatstats(self, event) -> None:
        try:
            messages = await self.context.client.get_messages(event.chat_id, limit=200)
        except Exception:  # noqa: BLE001
            await event.reply("خطا در دریافت پیام‌ها.")
            return
        counter = Counter()
        for m in messages:
            name = getattr(m.sender, "first_name", None) if m.sender else "—"
            counter[name] += 1
        lines = ["📊 آمار ۲۰۰ پیام اخیر:"]
        for name, count in counter.most_common(10):
            lines.append(f"• {name}: {count} پیام")
        await event.reply("\n".join(lines))


class UsageReportModule(BaseModule):
    metadata = ModuleMetadata(
        key="usage_report", name="گزارش مصرف", category="analytics",
        description="گزارش مصرف کاربر با /usage",
    )

    @handler("new_message", pattern=r"^/usage")
    async def on_usage(self, event) -> None:
        from sqlalchemy import func, select

        from app.billing.service import BillingService
        from app.database.models.automation import AutomationRule
        from app.database.models.modules import UserModule
        from app.database.models.scheduler import ScheduledTask
        from app.database.session import async_session_factory

        async with async_session_factory() as session:
            sub = await BillingService(session).subscriptions.active_for_user(self.context.user_id)
            plan = sub.plan.name if sub and sub.plan else "—"
            modules = await session.scalar(
                select(func.count()).select_from(UserModule).where(
                    UserModule.user_id == self.context.user_id, UserModule.enabled.is_(True)
                )
            )
            rules = await session.scalar(
                select(func.count()).select_from(AutomationRule).where(AutomationRule.user_id == self.context.user_id)
            )
            tasks = await session.scalar(
                select(func.count()).select_from(ScheduledTask).where(ScheduledTask.user_id == self.context.user_id)
            )
        await event.reply(
            "📊 گزارش مصرف\n\n"
            f"💎 اشتراک: {plan}\n"
            f"🧩 ماژول فعال: {modules or 0}\n"
            f"🤖 قانون اتوماسیون: {rules or 0}\n"
            f"⏰ وظیفه زمان‌بندی: {tasks or 0}"
        )


class RenameModule(BaseModule):
    metadata = ModuleMetadata(
        key="rename", name="تغییر نام فایل", category="media",
        description="تغییر نام فایل با ریپلای /rename نام جدید",
    )

    @handler("new_message", pattern=r"^/rename")
    async def on_rename(self, event) -> None:
        newname = (event.message.message or "")[7:].strip()
        if not newname or not event.message.is_reply:
            await event.reply("روی یک فایل ریپلای بزن و /rename نام جدید")
            return
        from telethon.tl.types import DocumentAttributeFilename

        replied = await event.message.get_reply_message()
        if replied.media is None:
            await event.reply("این پیام فایل نیست.")
            return
        try:
            data = await replied.download_media(file=bytes)
            await self.context.client.send_file(
                event.chat_id, data, force_document=True,
                attributes=[DocumentAttributeFilename(newname)],
                reply_to=event.message.id,
            )
        except Exception as exc:  # noqa: BLE001
            await event.reply(f"خطا: {exc}")


class AutoEditModule(BaseModule):
    metadata = ModuleMetadata(
        key="auto_edit", name="ویرایش خودکار", category="message",
        description="ویرایش پیام ارسالی پس از چند ثانیه",
        settings_schema={
            "delay": {"label": "تاخیر (ثانیه)", "type": "text", "default": "5"},
            "suffix": {"label": "متن افزوده", "type": "text", "default": " ✏️"},
        },
    )

    @handler("new_message", outgoing=True)
    async def on_outgoing(self, event) -> None:
        try:
            delay = int(self.setting("delay", "5"))
        except ValueError:
            delay = 5
        suffix = str(self.setting("suffix", " ✏️"))
        await asyncio.sleep(delay)
        try:
            await event.edit((event.message.message or "") + suffix)
        except Exception:  # noqa: BLE001
            pass
