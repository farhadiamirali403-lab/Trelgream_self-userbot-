"""More info/media tools: chat info, message info, links, file info, download."""

from __future__ import annotations

import re

from app.modules.base import BaseModule, ModuleMetadata, handler


class ChatInfoModule(BaseModule):
    metadata = ModuleMetadata(
        key="chat_info", name="اطلاعات چت", category="search",
        description="اطلاعات یک چت با /cinfo (یا /cinfo @username)",
    )

    @handler("new_message", pattern=r"^/cinfo")
    async def on_cinfo(self, event) -> None:
        arg = (event.message.message or "")[6:].strip()
        try:
            chat = await self.context.client.get_entity(arg) if arg else await event.get_chat()
        except Exception:  # noqa: BLE001
            await event.reply("چت یافت نشد.")
            return
        title = getattr(chat, "title", None) or f"{getattr(chat, 'first_name', '')} {getattr(chat, 'last_name', '')}".strip()
        await event.reply(
            "💬 اطلاعات چت\n\n"
            f"📝 عنوان: {title}\n"
            f"🆔 آیدی: {chat.id}\n"
            f"🔗 یوزرنیم: @{getattr(chat, 'username', None) or '—'}"
        )


class MessageInfoModule(BaseModule):
    metadata = ModuleMetadata(
        key="message_info", name="اطلاعات پیام", category="search",
        description="اطلاعات پیام با ریپلای /minfo",
    )

    @handler("new_message", pattern=r"^/minfo")
    async def on_minfo(self, event) -> None:
        if not event.message.is_reply:
            await event.reply("روی یک پیام ریپلای بزن و /minfo بفرست.")
            return
        m = await event.message.get_reply_message()
        sender = getattr(m.sender, "first_name", None) or "—"
        media = m.media.__class__.__name__.replace("MessageMedia", "") if m.media else "—"
        await event.reply(
            "📄 اطلاعات پیام\n\n"
            f"🆔 آیدی: {m.id}\n"
            f"👤 فرستنده: {sender}\n"
            f"📅 تاریخ: {m.date}\n"
            f"🎬 رسانه: {media}\n"
            f"💬 متن: {(m.message or '')[:100]}"
        )


class LinkExtractorModule(BaseModule):
    metadata = ModuleMetadata(
        key="link_extractor", name="استخراج لینک", category="search",
        description="استخراج لینک‌ها با ریپلای /links",
    )

    @handler("new_message", pattern=r"^/links")
    async def on_links(self, event) -> None:
        if not event.message.is_reply:
            await event.reply("روی یک پیام ریپلای بزن و /links بفرست.")
            return
        m = await event.message.get_reply_message()
        links = re.findall(r"https?://[^\s]+", m.message or "")
        if not links:
            await event.reply("لینکی یافت نشد.")
            return
        await event.reply("🔗 لینک‌ها:\n" + "\n".join(links))


class FileInfoModule(BaseModule):
    metadata = ModuleMetadata(
        key="file_info", name="اطلاعات فایل", category="media",
        description="اطلاعات فایل با ریپلای /fileinfo",
    )

    @handler("new_message", pattern=r"^/fileinfo")
    async def on_fileinfo(self, event) -> None:
        if not event.message.is_reply:
            await event.reply("روی یک فایل ریپلای بزن و /fileinfo بفرست.")
            return
        m = await event.message.get_reply_message()
        f = getattr(m, "file", None)
        if f is None:
            await event.reply("این پیام فایل ندارد.")
            return
        size = f.size or 0
        size_str = f"{size / 1024 / 1024:.2f} MB" if size > 1024 * 1024 else f"{size / 1024:.1f} KB"
        await event.reply(
            "📁 اطلاعات فایل\n\n"
            f"📝 نام: {getattr(f, 'name', None) or '—'}\n"
            f"📏 حجم: {size_str}\n"
            f"🔤 نوع: {getattr(f, 'mime_type', None) or '—'}"
        )


class DownloaderModule(BaseModule):
    metadata = ModuleMetadata(
        key="downloader", name="دانلودر", category="media",
        description="دانلود رسانه با ریپلای /dl",
    )

    @handler("new_message", pattern=r"^/dl")
    async def on_dl(self, event) -> None:
        if not event.message.is_reply:
            await event.reply("روی یک رسانه ریپلای بزن و /dl بفرست.")
            return
        m = await event.message.get_reply_message()
        if m.media is None:
            await event.reply("این پیام رسانه ندارد.")
            return
        await event.reply("⏳ در حال دانلود...")
        try:
            data = await m.download_media(file=bytes)
            await self.context.client.send_file(
                event.chat_id, data, caption="✅ دانلود شد", reply_to=event.message.id
            )
        except Exception as exc:  # noqa: BLE001
            await event.reply(f"خطا در دانلود: {exc}")
