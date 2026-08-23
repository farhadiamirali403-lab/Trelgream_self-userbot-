"""Information tools: user/group info, sessions, save, id, search."""

from __future__ import annotations

from telethon.tl.functions.account import GetAuthorizationsRequest

from app.modules.base import BaseModule, ModuleMetadata, handler


class UserInfoByIdModule(BaseModule):
    metadata = ModuleMetadata(
        key="user_info_by_id", name="اطلاعات کاربر با آیدی", category="search",
        description="اطلاعات کاربر با /uinfo آیدی (مثل /uinfo 123456789)",
    )

    @handler("new_message", pattern=r"^/uinfo")
    async def on_uinfo(self, event) -> None:
        raw = (event.message.message or "")[6:].strip()
        if not raw:
            await event.reply("استفاده: /uinfo آیدی")
            return
        try:
            entity = await self.context.client.get_entity(int(raw))
        except Exception:  # noqa: BLE001
            await event.reply("کاربر یافت نشد.")
            return
        name = f"{getattr(entity, 'first_name', '') or ''} {getattr(entity, 'last_name', '') or ''}".strip()
        await event.reply(
            "👤 اطلاعات کاربر\n\n"
            f"ID: {entity.id}\n"
            f"نام: {name}\n"
            f"یوزرنیم: @{getattr(entity, 'username', None) or '—'}\n"
            f"تلفن: {getattr(entity, 'phone', None) or '—'}"
        )


class GroupInfoModule(BaseModule):
    metadata = ModuleMetadata(
        key="group_info", name="دریافت اطلاعات گروه", category="search",
        description="اطلاعات گروه فعلی با /ginfo",
    )

    @handler("new_message", pattern=r"^/ginfo")
    async def on_ginfo(self, event) -> None:
        try:
            chat = await event.get_chat()
        except Exception:  # noqa: BLE001
            await event.reply("خطا در دریافت گروه.")
            return
        title = getattr(chat, "title", None) or "—"
        cid = getattr(chat, "id", None)
        username = getattr(chat, "username", None) or "—"
        members = "—"
        try:
            members = len(await self.context.client.get_participants(chat, limit=200))
        except Exception:  # noqa: BLE001
            pass
        await event.reply(
            "👥 اطلاعات گروه\n\n"
            f"📝 عنوان: {title}\n"
            f"🆔 آیدی: {cid}\n"
            f"🔗 یوزرنیم: @{username}\n"
            f"👤 اعضا (تقریبی): {members}"
        )


class SessionsModule(BaseModule):
    metadata = ModuleMetadata(
        key="sessions", name="نشست‌های فعال اکانت", category="search",
        description="نمایش نشست‌های فعال حساب با /sessions",
    )

    @handler("new_message", pattern=r"^/sessions")
    async def on_sessions(self, event) -> None:
        try:
            result = await self.context.client(GetAuthorizationsRequest())
        except Exception:  # noqa: BLE001
            await event.reply("خطا در دریافت نشست‌ها.")
            return
        lines = ["🔐 نشست‌های فعال:"]
        for a in result.authorizations:
            lines.append(
                f"• {getattr(a, 'device_model', '—')} — "
                f"{getattr(a, 'platform', '—')} {getattr(a, 'system_version', '')}"
            )
        await event.reply("\n".join(lines))


class SaveToPvModule(BaseModule):
    metadata = ModuleMetadata(
        key="save_to_pv", name="ذخیره در پیوی", category="search",
        description="ذخیره پیام در Saved Messages با ریپلای /save",
    )

    @handler("new_message", pattern=r"^/save")
    async def on_save(self, event) -> None:
        if not event.message.is_reply:
            await event.reply("روی یک پیام ریپلای بزن و /save بفرست.")
            return
        try:
            replied = await event.message.get_reply_message()
            await self.context.client.send_message("me", replied)
            await event.reply("✅ در Saved Messages ذخیره شد.")
        except Exception as exc:  # noqa: BLE001
            await event.reply(f"خطا در ذخیره: {exc}")


class PersonIdModule(BaseModule):
    metadata = ModuleMetadata(
        key="person_id", name="آیدی عددی شخص", category="search",
        description="آیدی عددی شخص با ریپلای /uid",
    )

    @handler("new_message", pattern=r"^/uid")
    async def on_uid(self, event) -> None:
        user = None
        if event.message.is_reply:
            try:
                replied = await event.message.get_reply_message()
                user = replied.sender
            except Exception:  # noqa: BLE001
                pass
        if user is None:
            await event.reply("روی پیام شخص ریپلای بزن و /uid بفرست.")
            return
        name = f"{getattr(user, 'first_name', '') or ''} {getattr(user, 'last_name', '') or ''}".strip()
        await event.reply(f"🆔 {name}\nآیدی عددی: {user.id}")


class ChatSearchModule(BaseModule):
    metadata = ModuleMetadata(
        key="search_text", name="جستجوی متن در چت", category="search",
        description="جستجوی متن با /search کلمه",
    )

    @handler("new_message", pattern=r"^/search")
    async def on_search(self, event) -> None:
        query = (event.message.message or "")[7:].strip()
        if not query:
            await event.reply("استفاده: /search متن")
            return
        try:
            messages = await self.context.client.get_messages(event.chat_id, search=query, limit=5)
        except Exception:  # noqa: BLE001
            await event.reply("خطا در جستجو.")
            return
        if not messages:
            await event.reply("نتیجه‌ای یافت نشد.")
            return
        lines = [f"🔍 نتایج جستجوی «{query}»:"]
        for m in messages:
            snippet = (m.message or "")[:60]
            sender = getattr(m.sender, "first_name", None) or "—"
            lines.append(f"• [{sender}] {snippet}")
        await event.reply("\n".join(lines))
