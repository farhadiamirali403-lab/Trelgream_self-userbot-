"""Market & misc tools: currency, gold, link button, enemy list."""

from __future__ import annotations

import httpx
from telethon import Button

from app.modules.base import BaseModule, ModuleMetadata, handler


async def _get_json(url: str, params: dict | None = None) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()
    except Exception:  # noqa: BLE001
        return None


class CurrencyModule(BaseModule):
    metadata = ModuleMetadata(
        key="currency", name="قیمت ارزها", category="market",
        description="نمایش قیمت ارزهای دیجیتال با /currency",
    )

    @handler("new_message", pattern=r"^/currency")
    async def on_currency(self, event) -> None:
        data = await _get_json(
            "https://api.coingecko.com/api/v3/simple/price",
            {"ids": "bitcoin,ethereum,toncoin,tether", "vs_currencies": "usd"},
        )
        if not data:
            await event.reply("خطا در دریافت قیمت ارزها.")
            return
        btc = data.get("bitcoin", {}).get("usd")
        eth = data.get("ethereum", {}).get("usd")
        ton = data.get("toncoin", {}).get("usd")
        usdt = data.get("tether", {}).get("usd")
        text = "💰 قیمت ارزها (USD)\n\n"
        if btc:
            text += f"₿ بیت‌کوین: ${btc:,.2f}\n"
        if eth:
            text += f"Ξ اتریوم: ${eth:,.2f}\n"
        if ton:
            text += f"💎 تون: ${ton:,.4f}\n"
        if usdt:
            text += f"💵 تتر: ${usdt:,.4f}\n"
        await event.reply(text)


class GoldModule(BaseModule):
    metadata = ModuleMetadata(
        key="gold", name="قیمت طلا", category="market",
        description="نمایش قیمت طلا با /gold",
    )

    @handler("new_message", pattern=r"^/gold")
    async def on_gold(self, event) -> None:
        data = await _get_json("https://data-asg.goldprice.org/dbXRates/USD")
        if not data or not data.get("items"):
            await event.reply("خطا در دریافت قیمت طلا.")
            return
        try:
            xau = data["items"][0]["xauPrice"]
            per_gram = xau / 31.1035
            await event.reply(
                f"🥇 قیمت طلا (جهانی)\n\n"
                f"انس: ${xau:,.2f}\n"
                f"گرم: ${per_gram:,.2f}"
            )
        except Exception:  # noqa: BLE001
            await event.reply("خطا در پردازش قیمت طلا.")


class LinkButtonModule(BaseModule):
    metadata = ModuleMetadata(
        key="link_button", name="متن با دکمه لینک", category="message",
        description="ساخت متن با دکمه لینک: /btn متن | لینک",
    )

    @handler("new_message", pattern=r"^/btn")
    async def on_btn(self, event) -> None:
        raw = (event.message.message or "")[4:].strip()
        if "|" not in raw:
            await event.reply("استفاده: /btn متن | https://لینک")
            return
        text, url = raw.split("|", 1)
        text, url = text.strip(), url.strip()
        if not url.startswith("http"):
            await event.reply("لینک باید با http شروع شود.")
            return
        await event.reply(text, buttons=[[Button.url("🔗 لینک", url)]])


class EnemyModule(BaseModule):
    metadata = ModuleMetadata(
        key="enemy", name="دشمن/بدخواه", category="message",
        description="افزودن دشمن با /enemy و لیست با /enemies",
    )

    @handler("new_message", pattern=r"^/enemy")
    async def on_enemy_cmd(self, event) -> None:
        text = (event.message.message or "").strip()
        parts = text.split(maxsplit=1)
        cmd = parts[0]
        arg = parts[1].strip() if len(parts) > 1 else ""
        if cmd == "/enemies":
            enemies = list(self.setting("enemies", []) or [])
            if not enemies:
                await event.reply("دشمنی ثبت نشده.")
            else:
                await event.reply("⚔️ لیست دشمنان:\n" + "\n".join(f"• {e}" for e in enemies))
            return
        if not arg:
            await event.reply("استفاده: /enemy آیدی یا @username")
            return
        try:
            entity = await self.context.client.get_entity(arg)
        except Exception:  # noqa: BLE001
            await event.reply("کاربر یافت نشد.")
            return
        enemies = list(self.setting("enemies", []) or [])
        if entity.id not in enemies:
            enemies.append(entity.id)
            await self.persist_setting("enemies", enemies)
        name = getattr(entity, "first_name", None) or entity.id
        await event.reply(f"✅ {name} به دشمنان اضافه شد.")

    @handler("new_message")
    async def on_message_check(self, event) -> None:
        msg = event.message.message or ""
        if msg.startswith("/"):
            return
        enemies = list(self.setting("enemies", []) or [])
        if event.sender_id in enemies:
            try:
                await self.context.client.send_read_acknowledge(event.chat_id)
            except Exception:  # noqa: BLE001
                pass
