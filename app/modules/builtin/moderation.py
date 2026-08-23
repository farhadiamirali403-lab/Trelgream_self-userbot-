"""Group moderation modules: mute, unmute, ban, unban, kick, purge, warn."""

from __future__ import annotations

from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights

from app.modules.base import BaseModule, ModuleMetadata, handler


async def _resolve_target(client, event, arg: str):
    if event.message.is_reply:
        replied = await event.message.get_reply_message()
        return replied.sender
    if arg:
        return await client.get_entity(arg)
    return None


async def _apply_rights(event, client, user_id, rights, ok_msg: str) -> None:
    try:
        await client(EditBannedRequest(event.chat_id, user_id, rights))
        await event.reply(ok_msg)
    except Exception as exc:  # noqa: BLE001
        await event.reply(f"⚠️ خطا (نیاز به دسترسی ادمین): {exc}")


class MuteModule(BaseModule):
    metadata = ModuleMetadata(
        key="mute", name="سکوت", category="groups",
        description="ساکت کردن کاربر (ریپلای یا /mute @user)",
    )

    @handler("new_message", pattern=r"^/mute")
    async def on_mute(self, event) -> None:
        arg = (event.message.message or "")[5:].strip()
        target = await _resolve_target(self.context.client, event, arg)
        if target is None:
            await event.reply("روی پیام کاربر ریپلای بزن یا /mute @username")
            return
        await _apply_rights(
            event, self.context.client, target.id,
            ChatBannedRights(until_date=None, send_messages=True),
            f"✅ {getattr(target, 'first_name', target.id)} ساکت شد.",
        )


class UnmuteModule(BaseModule):
    metadata = ModuleMetadata(
        key="unmute", name="لغو سکوت", category="groups",
        description="رفع سکوت کاربر (ریپلای یا /unmute @user)",
    )

    @handler("new_message", pattern=r"^/unmute")
    async def on_unmute(self, event) -> None:
        arg = (event.message.message or "")[7:].strip()
        target = await _resolve_target(self.context.client, event, arg)
        if target is None:
            await event.reply("روی پیام کاربر ریپلای بزن یا /unmute @username")
            return
        await _apply_rights(
            event, self.context.client, target.id,
            ChatBannedRights(until_date=None),
            f"✅ سکوت {getattr(target, 'first_name', target.id)} برداشته شد.",
        )


class BanModule(BaseModule):
    metadata = ModuleMetadata(
        key="ban", name="بن", category="groups",
        description="بن کردن کاربر (ریپلای یا /ban @user)",
    )

    @handler("new_message", pattern=r"^/ban")
    async def on_ban(self, event) -> None:
        arg = (event.message.message or "")[4:].strip()
        target = await _resolve_target(self.context.client, event, arg)
        if target is None:
            await event.reply("روی پیام کاربر ریپلای بزن یا /ban @username")
            return
        await _apply_rights(
            event, self.context.client, target.id,
            ChatBannedRights(until_date=None, view_messages=True),
            f"🔨 {getattr(target, 'first_name', target.id)} بن شد.",
        )


class UnbanModule(BaseModule):
    metadata = ModuleMetadata(
        key="unban", name="آنبن", category="groups",
        description="رفع بن کاربر (ریپلای یا /unban @user)",
    )

    @handler("new_message", pattern=r"^/unban")
    async def on_unban(self, event) -> None:
        arg = (event.message.message or "")[6:].strip()
        target = await _resolve_target(self.context.client, event, arg)
        if target is None:
            await event.reply("روی پیام کاربر ریپلای بزن یا /unban @username")
            return
        await _apply_rights(
            event, self.context.client, target.id,
            ChatBannedRights(until_date=None),
            f"✅ بن {getattr(target, 'first_name', target.id)} برداشته شد.",
        )


class KickModule(BaseModule):
    metadata = ModuleMetadata(
        key="kick", name="اخراج", category="groups",
        description="اخراج کاربر (ریپلای یا /kick @user)",
    )

    @handler("new_message", pattern=r"^/kick")
    async def on_kick(self, event) -> None:
        arg = (event.message.message or "")[5:].strip()
        target = await _resolve_target(self.context.client, event, arg)
        if target is None:
            await event.reply("روی پیام کاربر ریپلای بزن یا /kick @username")
            return
        try:
            await self.context.client(
                EditBannedRequest(event.chat_id, target.id, ChatBannedRights(until_date=None, view_messages=True))
            )
            await self.context.client(
                EditBannedRequest(event.chat_id, target.id, ChatBannedRights(until_date=None))
            )
            await event.reply(f"👢 {getattr(target, 'first_name', target.id)} اخراج شد.")
        except Exception as exc:  # noqa: BLE001
            await event.reply(f"⚠️ خطا (نیاز به دسترسی ادمین): {exc}")


class PurgeModule(BaseModule):
    metadata = ModuleMetadata(
        key="purge", name="پاکسازی", category="groups",
        description="حذف پیام‌ها با ریپلای /purge",
    )

    @handler("new_message", pattern=r"^/purge")
    async def on_purge(self, event) -> None:
        if not event.message.is_reply:
            await event.reply("روی یک پیام ریپلای بزن و /purge بفرست.")
            return
        replied = await event.message.get_reply_message()
        msgs = await self.context.client.get_messages(event.chat_id, min_id=replied.id)
        ids = [m.id for m in msgs] + [replied.id, event.message.id]
        await self.context.client.delete_messages(event.chat_id, ids)
        await event.reply(f"🧹 {len(ids)} پیام پاک شد.")


class WarnModule(BaseModule):
    metadata = ModuleMetadata(
        key="warn", name="اخطار", category="groups",
        description="اخطار کاربر با /warn و مشاهده با /warns",
    )

    @handler("new_message", pattern=r"^/warn")
    async def on_warn(self, event) -> None:
        arg = (event.message.message or "")[5:].strip()
        target = await _resolve_target(self.context.client, event, arg)
        if target is None:
            await event.reply("روی پیام کاربر ریپلای بزن یا /warn @username")
            return
        warns = dict(self.setting("warns", {}) or {})
        warns[str(target.id)] = warns.get(str(target.id), 0) + 1
        await self.persist_setting("warns", warns)
        await event.reply(f"⚠️ {getattr(target, 'first_name', target.id)} اخطار گرفت ({warns[str(target.id)]}/3).")

    @handler("new_message", pattern=r"^/warns")
    async def on_warns(self, event) -> None:
        arg = (event.message.message or "")[6:].strip()
        target = await _resolve_target(self.context.client, event, arg)
        if target is None:
            await event.reply("روی پیام کاربر ریپلای بزن یا /warns @username")
            return
        warns = dict(self.setting("warns", {}) or {})
        count = warns.get(str(target.id), 0)
        await event.reply(f"⚠️ {getattr(target, 'first_name', target.id)}: {count} اخطار.")
