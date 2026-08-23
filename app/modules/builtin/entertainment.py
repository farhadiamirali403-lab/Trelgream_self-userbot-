"""Entertainment & utility modules: wiki, weather, music, image/gif, calc, time, app."""

from __future__ import annotations

import ast
from datetime import datetime
from urllib.parse import quote

import httpx

from app.modules.base import BaseModule, ModuleMetadata, handler


async def _get_json(url: str, params: dict | None = None) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()
    except Exception:  # noqa: BLE001
        return None


class WikiModule(BaseModule):
    metadata = ModuleMetadata(
        key="wiki", name="جستجوی ویکی‌پدیا", category="entertainment",
        description="جستجو در ویکی‌پدیا فارسی با /wiki متن",
    )

    @handler("new_message", pattern=r"^/wiki")
    async def on_wiki(self, event) -> None:
        query = (event.message.message or "")[5:].strip()
        if not query:
            await event.reply("استفاده: /wiki متن جستجو")
            return
        data = await _get_json(
            "https://fa.wikipedia.org/w/api.php",
            {"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": 1},
        )
        if not data:
            await event.reply("خطا در دریافت اطلاعات.")
            return
        results = (data.get("query") or {}).get("search", [])
        if not results:
            await event.reply("نتیجه‌ای یافت نشد.")
            return
        r = results[0]
        import re

        snippet = re.sub(r"<[^>]+>", "", r.get("snippet", ""))
        link = f"https://fa.wikipedia.org/wiki/{quote(r['title'])}"
        await event.reply(f"📖 {r['title']}\n\n{snippet}...\n\n{link}")


class WeatherModule(BaseModule):
    metadata = ModuleMetadata(
        key="weather", name="وضعیت آب‌وهوا", category="entertainment",
        description="نمایش آب‌وهوا با /weather نام شهر",
    )

    @handler("new_message", pattern=r"^/weather")
    async def on_weather(self, event) -> None:
        city = (event.message.message or "")[8:].strip()
        if not city:
            await event.reply("استفاده: /weather تهران")
            return
        data = await _get_json(f"https://wttr.in/{quote(city)}?format=j1")
        if not data:
            await event.reply("خطا در دریافت آب‌وهوا.")
            return
        try:
            cur = data["current_condition"][0]
            area = data.get("nearest_area", [{}])[0].get("areaName", [{}])[0].get("value", city)
            text = (
                f"🌤 آب‌وهوای {area}\n\n"
                f"🌡 دما: {cur['temp_C']}°C\n"
                f"📝 وضعیت: {cur['lang_fa'][0]['value'] if cur.get('lang_fa') else cur['weatherDesc'][0]['value']}\n"
                f"💧 رطوبت: {cur['humidity']}%\n"
                f"💨 باد: {cur['windspeedKmph']} km/h\n"
            )
        except Exception:  # noqa: BLE001
            text = "خطا در پردازش داده آب‌وهوا."
        await event.reply(text)


class MusicModule(BaseModule):
    metadata = ModuleMetadata(
        key="music", name="موسیقی دلخواه", category="entertainment",
        description="جستجوی موسیقی با /music نام آهنگ",
    )

    @handler("new_message", pattern=r"^/music")
    async def on_music(self, event) -> None:
        name = (event.message.message or "")[6:].strip()
        if not name:
            await event.reply("استفاده: /music نام آهنگ")
            return
        data = await _get_json("https://itunes.apple.com/search", {"term": name, "media": "music", "limit": 1})
        if not data or not data.get("results"):
            await event.reply("آهنگی یافت نشد.")
            return
        track = data["results"][0]
        text = (
            f"🎵 {track['trackName']}\n"
            f"🎤 {track['artistName']}\n"
            f"💿 {track.get('collectionName', '')}\n\n"
            f"🎧 پیش‌نمایش: {track['previewUrl']}\n"
            f"🔗 {track.get('trackViewUrl', '')}"
        )
        await event.reply(text)


class ImageSearchModule(BaseModule):
    metadata = ModuleMetadata(
        key="image_search", name="عکس مرتبط با متن", category="entertainment",
        description="جستجوی عکس با /img متن",
    )

    @handler("new_message", pattern=r"^/img")
    async def on_img(self, event) -> None:
        text = (event.message.message or "")[4:].strip()
        if not text:
            await event.reply("استفاده: /img متن")
            return
        try:
            results = await self.context.client.inline_query("@pic", text)
            if results and results[0].photo:
                await self.context.client.send_file(event.chat_id, results[0].photo, reply_to=event.message.id)
            else:
                await event.reply("عکسی یافت نشد.")
        except Exception as exc:  # noqa: BLE001
            await event.reply(f"خطا در جستجوی عکس: {exc}")


class GifSearchModule(BaseModule):
    metadata = ModuleMetadata(
        key="gif_search", name="گیف مرتبط با متن", category="entertainment",
        description="جستجوی گیف با /gif متن",
    )

    @handler("new_message", pattern=r"^/gif")
    async def on_gif(self, event) -> None:
        text = (event.message.message or "")[4:].strip()
        if not text:
            await event.reply("استفاده: /gif متن")
            return
        try:
            results = await self.context.client.inline_query("@gif", text)
            if results and results[0].document:
                await self.context.client.send_file(event.chat_id, results[0].document, reply_to=event.message.id)
            else:
                await event.reply("گیفی یافت نشد.")
        except Exception as exc:  # noqa: BLE001
            await event.reply(f"خطا در جستجوی گیف: {exc}")


class CalcModule(BaseModule):
    metadata = ModuleMetadata(
        key="calc", name="ماشین حساب", category="entertainment",
        description="محاسبه با /calc عبارت (مثل /calc 2+3*4)",
    )

    @handler("new_message", pattern=r"^/calc")
    async def on_calc(self, event) -> None:
        expr = (event.message.message or "")[5:].strip()
        if not expr:
            await event.reply("استفاده: /calc 2+3*4")
            return
        allowed = set("0123456789+-*/().% ")
        if any(c not in allowed for c in expr):
            await event.reply("عبارت نامعتبر است.")
            return
        try:
            result = eval(expr, {"__builtins__": {}}, {})  # noqa: S307
            await event.reply(f"🧮 {expr} = {result}")
        except Exception:  # noqa: BLE001
            await event.reply("عبارت نامعتبر است.")


class TimeModule(BaseModule):
    metadata = ModuleMetadata(
        key="time", name="دریافت ساعت", category="entertainment",
        description="نمایش ساعت با /time",
    )

    @handler("new_message", pattern=r"^/time")
    async def on_time(self, event) -> None:
        from datetime import timezone, timedelta

        now_utc = datetime.now(timezone.utc)
        tehran = now_utc.astimezone(timezone(timedelta(hours=3, minutes=30)))
        await event.reply(
            f"🕐 ساعت\n\n🇮🇷 تهران: {tehran.strftime('%H:%M:%S')}\n"
            f"🌍 UTC: {now_utc.strftime('%H:%M:%S')}\n"
            f"📅 تاریخ: {tehran.strftime('%Y-%m-%d')}"
        )


class AppInfoModule(BaseModule):
    metadata = ModuleMetadata(
        key="app_info", name="دریافت اپلیکیشن", category="entertainment",
        description="نمایش اطلاعات اپلیکیشن/حساب با /app",
    )

    @handler("new_message", pattern=r"^/app")
    async def on_app(self, event) -> None:
        try:
            me = await self.context.client.get_me()
        except Exception:  # noqa: BLE001
            me = None
        name = f"{getattr(me, 'first_name', '') or ''} {getattr(me, 'last_name', '') or ''}".strip()
        await event.reply(
            "🤖 اطلاعات اپلیکیشن\n\n"
            f"👤 حساب: {name or '—'}\n"
            f"🆔 آیدی: {getattr(me, 'id', '—')}\n"
            "📱 دستگاه: TelegramSaaS\n"
            "🔧 نسخه: 1.0\n"
            "🌐 پلتفرم: Telegram Userbot SaaS"
        )
