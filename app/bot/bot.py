"""Central Telegram bot: Persian UI, auth flow, billing, panel."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from telethon import Button, TelegramClient, events

from app.automation.repository import AutomationRuleRepository
from app.billing.repositories import PlanRepository
from app.billing.service import BillingService
from app.bot import keyboards as kb
from app.bot import texts as tx
from app.bot.state import ConversationState
from app.core.config import Settings
from app.core.logging import get_logger
from app.core.redis import AuthStateStore, RateLimiter, get_redis
from app.core.security import CommandSigner, SessionCipher
from app.database.session import async_session_factory
from app.modules.manager import ModuleManager
from app.modules.registry import registry
from app.scheduler.repository import ScheduledTaskRepository
from app.scheduler.service import ScheduledTaskService
from app.storage.factory import get_storage
from app.telegram.auth_service import TelegramAuthService
from app.userbots.service import UserbotService
from app.users.service import UserService
from app.workers.commands import CommandBus

log = get_logger("bot")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d") if dt else "—"


class CentralBot:
    def __init__(self, settings: Settings, client: TelegramClient) -> None:
        self.settings = settings
        self.client = client
        self.redis = get_redis()
        self.cipher = SessionCipher(settings.session_encryption_key)
        self.state = ConversationState(self.redis)
        self.rate = RateLimiter(self.redis)
        self.auth_store = AuthStateStore(self.redis, self.cipher.encrypt, self.cipher.decrypt)
        self.auth_service = TelegramAuthService(self.auth_store, self.cipher, settings)
        self.command_bus = CommandBus(self.redis, CommandSigner(settings.session_encryption_key or "cmd"))
        self.storage = get_storage()

    # ------------------------------------------------------------------ setup

    def register_handlers(self) -> None:
        for pattern, handler in [
            ("/start", self.on_start),
            ("/help", self.on_help),
            ("/panel", self.on_panel),
            ("/account", self.on_account),
            ("/subscription", self.on_subscription),
            ("/userbot", self.on_userbot),
            ("/settings", self.on_settings),
            ("/support", self.on_support),
        ]:
            self.client.add_event_handler(handler, events.NewMessage(pattern=pattern))
        self.client.add_event_handler(self.on_message, events.NewMessage(incoming=True))
        self.client.add_event_handler(self.on_callback, events.CallbackQuery())

    async def run(self) -> None:
        self.register_handlers()
        while True:
            try:
                await self.client.start(bot_token=self.settings.central_bot_token)
                me = await self.client.get_me()
                log.info("Central bot started", extra_fields={"username": me.username})
                await self.client.run_until_disconnected()
                log.warning("Central bot disconnected; reconnecting")
            except ConnectionError as exc:
                log.warning(
                    "Telegram connection failed; retrying in 15s",
                    extra_fields={"error": str(exc)},
                )
            except Exception as exc:  # noqa: BLE001
                log.error("Central bot error; retrying in 15s", extra_fields={"error": str(exc)})
            await asyncio.sleep(15)

    # ------------------------------------------------------------------ commands

    async def on_start(self, event) -> None:
        tg_id = event.sender_id
        user = await self._user_from_event(event)
        await event.respond(tx.START, buttons=kb.main_panel())
        await self.state.clear(tg_id)

    async def on_help(self, event) -> None:
        await event.respond(tx.HELP, buttons=kb.back_panel())

    async def on_panel(self, event) -> None:
        await self._send_panel(event.sender_id, event)

    async def on_account(self, event) -> None:
        async with async_session_factory() as session:
            user = await UserService(session).repo.get_by_telegram_id(event.sender_id)
            if user is None:
                await event.respond(tx.NOT_AUTHORIZED)
                return
            status = "فعال" if (user.is_active and not user.is_suspended) else "غیرفعال"
            await event.respond(
                tx.ACCOUNT_INFO.format(
                    id=user.id,
                    username=user.username or "—",
                    phone=user.phone or "—",
                    status=status,
                ),
                buttons=kb.account_panel(),
            )

    async def on_subscription(self, event) -> None:
        async with async_session_factory() as session:
            subs = BillingService(session)
            active = await subs.subscriptions.active_for_user(event.sender_id)
            if active is None:
                await event.respond(tx.NO_SUBSCRIPTION, buttons=kb.subscription_panel())
                return
            await event.respond(
                tx.SUBSCRIPTION_INFO.format(
                    plan=active.plan.name,
                    status=tx.SUBSCRIPTION_STATUS.get(active.status, active.status),
                    started=_fmt(active.started_at),
                    expires=_fmt(active.expires_at),
                ),
                buttons=kb.subscription_panel(),
            )

    async def on_userbot(self, event) -> None:
        tg_id = event.sender_id
        async with async_session_factory() as session:
            from app.database.models.userbots import Userbot
            from sqlalchemy import select

            user = await UserService(session).repo.get_by_telegram_id(tg_id)
            stmt = select(Userbot).where(Userbot.user_id == user.id).order_by(Userbot.id.desc()) if user else None
            userbot = (await session.execute(stmt)).scalars().first() if stmt is not None else None

            if userbot is None:
                await event.respond(
                    tx.USERBOT_INFO.format(status="—", heartbeat="—"),
                    buttons=kb.userbot_panel(has_account=False),
                )
                return
            status = tx.USERBOT_STATUS_EMOJI.get(userbot.status, userbot.status)
            await event.respond(
                tx.USERBOT_INFO.format(
                    status=status,
                    heartbeat=_fmt(userbot.last_heartbeat_at),
                ),
                buttons=kb.userbot_panel(has_account=True),
            )

    async def on_settings(self, event) -> None:
        tg_id = event.sender_id if hasattr(event, "sender_id") else event.query.user_id
        async with async_session_factory() as session:
            user = await UserService(session).repo.get_by_telegram_id(tg_id)
            if user is None:
                await event.respond(tx.NOT_AUTHORIZED, buttons=kb.back_panel())
                return
            sub = await BillingService(session).subscriptions.active_for_user(user.id)
        text = (
            "⚙️ تنظیمات\n\n"
            f"👤 حساب: @{user.username or '—'}\n"
            f"📱 تلفن: {user.phone or '—'}\n"
            f"💎 اشتراک: {sub.plan.name if sub else '—'}\n\n"
            "برای تغییر هر بخش از منوی اصلی استفاده کنید."
        )
        await event.respond(text, buttons=kb.back_panel())

    async def on_support(self, event) -> None:
        tg_id = event.sender_id if hasattr(event, "sender_id") else event.query.user_id
        await self.state.set(tg_id, "awaiting_support", {})
        await event.respond("🆘 پیام خود را برای پشتیبانی بنویسید:", buttons=kb.cancel())

    # ------------------------------------------------------------------ callbacks

    async def on_callback(self, event) -> None:
        data = event.data.decode()
        tg_id = event.query.user_id
        await event.answer()

        if data == "back_panel":
            await self._send_panel(tg_id, event, edit=True)
        elif data == "cancel":
            await self.state.clear(tg_id)
            await self._send_panel(tg_id, event, edit=True)
        elif data == "ub":
            await self.on_userbot(event)
        elif data == "subscription":
            await self.on_subscription(event)
        elif data == "buy_plan":
            await self._show_plans(event)
        elif data.startswith("plan:"):
            await self._show_plan(event, int(data.split(":", 1)[1]))
        elif data.startswith("pay:"):
            await self._start_payment(event, int(data.split(":", 1)[1]))
        elif data == "auth_start":
            await self._start_auth(event)
        elif data == "modules":
            await self._show_modules(event)
        elif data.startswith("mod_cat:"):
            await self._show_category(event, data.split(":", 1)[1])
        elif data.startswith("mod_toggle:"):
            await self._toggle_module(event, int(data.split(":", 1)[1]))
        elif data.startswith("mod_ni:"):
            await event.answer("⏳ این قابلیت هنوز پیاده‌سازی نشده است (NOT IMPLEMENTED)")
        elif data.startswith("mod_config:"):
            await self._show_module_config(event, int(data.split(":", 1)[1]))
        elif data.startswith("set_text:"):
            parts = data.split(":")
            await self._ask_setting_text(event, int(parts[1]), parts[2])
        elif data.startswith("set_choice:"):
            parts = data.split(":")
            await self._save_choice(event, int(parts[1]), parts[2], parts[3])
        elif data.startswith("kw_add:"):
            await self._ask_keyword(event, int(data.split(":", 1)[1]))
        elif data.startswith("kw_del:"):
            parts = data.split(":")
            await self._del_keyword(event, int(parts[1]), int(parts[2]))
        elif data == "automation":
            await self._show_automation(event)
        elif data == "auto_add":
            await self._ask_auto_condition(event)
        elif data.startswith("auto_del:"):
            await self._del_rule(event, int(data.split(":", 1)[1]))
        elif data == "scheduler":
            await self._show_scheduler(event)
        elif data == "sched_add":
            await self._ask_sched_text(event)
        elif data.startswith("sched_del:"):
            await self._del_task(event, int(data.split(":", 1)[1]))
        elif data == "stats":
            await self._show_stats(event)
        elif data == "settings":
            await self.on_settings(event)
        elif data == "support":
            await self.on_support(event)
        else:
            await self._send_panel(tg_id, event, edit=True)

    # ------------------------------------------------------------------ auth flow

    async def _start_auth(self, event) -> None:
        tg_id = event.sender_id if hasattr(event, "sender_id") else event.query.user_id
        link = f"{self.settings.resolve_web_base_url()}/auth?tg={tg_id}"
        await event.respond(tx.AUTH_WEB_LINK.format(link=link), buttons=kb.cancel())

    async def on_message(self, event) -> None:
        if event.message.message and event.message.message.startswith("/"):
            return
        tg_id = event.sender_id
        current = await self.state.get(tg_id)
        if current is None:
            return
        state, data = current
        try:
            if state == "awaiting_phone":
                await self._handle_phone(event)
            elif state == "awaiting_code":
                await self._handle_code(event, data)
            elif state == "awaiting_2fa":
                await self._handle_2fa(event, data)
            elif state == "awaiting_receipt":
                await self._handle_receipt(event, data)
            elif state == "mod_setting":
                await self._handle_setting_text(event, data)
            elif state == "kw_setting":
                await self._handle_keyword(event, data)
            elif state == "auto_cond":
                await self._handle_auto_cond(event, data)
            elif state == "auto_reply":
                await self._handle_auto_reply(event, data)
            elif state == "sched_text":
                await self._handle_sched_text(event, data)
            elif state == "sched_time":
                await self._handle_sched_time(event, data)
            elif state == "awaiting_support":
                await self._handle_support(event, data)
        except Exception as exc:  # noqa: BLE001
            log.error("bot message handling failed", extra_fields={"error": str(exc)})
            await event.respond(f"⚠️ خطا: {exc}", buttons=kb.cancel())
            await self.state.clear(tg_id)

    async def _handle_phone(self, event) -> None:
        tg_id = event.sender_id
        phone = (event.message.message or "").strip()
        if not phone.startswith("+") or len(phone) < 8:
            await event.respond("شماره نامعتبر است. مثال: <code>+989xxxxxxxxx</code>", buttons=kb.cancel())
            return
        await self.rate.check(f"login:{tg_id}", self.settings.login_rate_limit, 300)
        result = await self.auth_service.send_code(phone)
        await self.state.set(tg_id, "awaiting_code", {"phone": phone})
        await event.respond(tx.ASK_CODE.format(message=result.message), buttons=kb.cancel())

    async def _handle_code(self, event, data: dict) -> None:
        tg_id = event.sender_id
        code = (event.message.message or "").strip()
        phone = data["phone"]
        await self.rate.check(f"code:{tg_id}", self.settings.code_verify_rate_limit, 600)
        result = await self.auth_service.sign_in_code(phone, code)
        if result.status == "needs_2fa":
            await self.state.set(tg_id, "awaiting_2fa", {"phone": phone})
            await event.respond(tx.ASK_2FA, buttons=kb.cancel())
            return
        await self._complete_auth(event, phone, result.session_string)

    async def _handle_2fa(self, event, data: dict) -> None:
        tg_id = event.sender_id
        password = (event.message.message or "").strip()
        phone = data["phone"]
        result = await self.auth_service.sign_in_2fa(phone, password)
        await self._complete_auth(event, phone, result.session_string)

    async def _complete_auth(self, event, phone: str, session_string: str) -> None:
        tg_id = event.sender_id
        async with async_session_factory() as session:
            user = await UserService(session).get_or_create(tg_id, username=event.sender.username or None)
            user.phone = phone
            service = UserbotService(session, self.cipher, self.command_bus)
            userbot = await service.complete_authorization(user.id, phone, session_string)
            await service.request_start(userbot.id, actor_id=user.id, actor_role="USER")
            await session.commit()
        await self.state.clear(tg_id)
        await event.respond(tx.AUTH_SUCCESS, buttons=kb.main_panel())

    # ------------------------------------------------------------------ billing

    async def _show_plans(self, event) -> None:
        async with async_session_factory() as session:
            plans = await PlanRepository(session).list_active()
        await event.respond("💎 انتخاب پلن:", buttons=kb.plans_keyboard(plans))

    async def _show_plan(self, event, plan_id: int) -> None:
        async with async_session_factory() as session:
            plan = await PlanRepository(session).get_or_raise(plan_id)
        await event.respond(
            tx.PLAN_DETAIL.format(
                name=plan.name,
                description=plan.description or "",
                price=plan.price,
                days=plan.duration_days,
                userbots=plan.max_userbots,
                modules=plan.max_modules,
            ),
            buttons=kb.plan_detail(plan.id),
        )

    async def _start_payment(self, event, plan_id: int) -> None:
        tg_id = event.query.user_id if hasattr(event, "query") else event.sender_id
        async with async_session_factory() as session:
            user = await UserService(session).get_or_create(tg_id)
            payment = await BillingService(session).purchase(user.id, plan_id)
            await session.commit()
            reference = payment.reference
            amount = payment.amount
        card = self.settings.payment_card_number or "—"
        owner = self.settings.payment_card_owner or "—"
        await self.state.set(tg_id, "awaiting_receipt", {"payment_id": payment.id})
        await event.respond(
            tx.PAYMENT_CARD.format(amount=amount, card_number=card, card_owner=owner),
            buttons=kb.cancel(),
        )

    async def _handle_receipt(self, event, data: dict) -> None:
        tg_id = event.sender_id
        media = event.message.media
        if media is None:
            await event.respond("لطفاً تصویر یا فایل رسید را ارسال کنید.", buttons=kb.cancel())
            return
        file_bytes = await event.message.download_media(file=bytes)
        if not file_bytes:
            await event.respond("دریافت رسید ناموفق بود.", buttons=kb.cancel())
            return

        payment_id = int(data["payment_id"])
        is_photo = bool(getattr(media, "photo", None))
        ext = ".jpg" if is_photo else ".bin"
        storage_key = f"receipts/payment_{payment_id}{ext}"

        async with async_session_factory() as session:
            await BillingService(session).add_receipt(
                payment_id,
                storage_key=storage_key,
                file_name=f"receipt{ext}",
                mime_type="image/jpeg" if ext == ".jpg" else "application/octet-stream",
                size=len(file_bytes),
            )
            payment = await BillingService(session).payments.get_or_raise(payment_id)
            reference = payment.reference
            await session.commit()
        await self.storage.save(storage_key, file_bytes, "image/jpeg")
        await self.state.clear(tg_id)
        await event.respond(tx.PAYMENT_SUBMITTED.format(reference=reference), buttons=kb.main_panel())

    # ------------------------------------------------------------------ modules

    async def _show_modules(self, event) -> None:
        from collections import defaultdict

        from app.modules.builtin.catalog import CATEGORY_NAMES

        counts: dict = defaultdict(int)
        for cls in registry.all():
            counts[cls.metadata.category] += 1
        rows = []
        for cat, name in CATEGORY_NAMES.items():
            if counts.get(cat, 0):
                rows.append([Button.inline(f"{name} ({counts[cat]})", f"mod_cat:{cat}".encode())])
        rows.append([Button.inline("🔙 بازگشت", b"back_panel")])
        text = "🧩 قابلیت‌ها\n\nیک دسته را انتخاب کنید:"
        if hasattr(event, "edit"):
            await event.edit(text, buttons=rows)
        else:
            await event.respond(text, buttons=rows)

    async def _show_category(self, event, category: str) -> None:
        tg_id = event.sender_id if hasattr(event, "sender_id") else event.query.user_id
        from sqlalchemy import select

        from app.database.models.modules import Module, UserModule
        from app.modules.builtin.catalog import CATEGORY_NAMES

        async with async_session_factory() as session:
            user = await UserService(session).repo.get_by_telegram_id(tg_id)
            if user is None:
                await event.respond(tx.NOT_AUTHORIZED, buttons=kb.back_panel())
                return
            modules = (
                await session.execute(
                    select(Module).where(Module.category == category).order_by(Module.id)
                )
            ).scalars().all()
            enabled_ids = {
                um.module_id
                for um in (
                    await session.execute(
                        select(UserModule).where(
                            UserModule.user_id == user.id, UserModule.enabled.is_(True)
                        )
                    )
                ).scalars().all()
            }
        rows = []
        for m in modules:
            cls = registry.get(m.key)
            not_impl = cls.metadata.not_implemented if cls else False
            if not_impl:
                rows.append([Button.inline(f"⏳ {m.name}", f"mod_ni:{m.id}".encode())])
                continue
            is_on = m.id in enabled_ids
            row = [Button.inline(f"{'✅' if is_on else '❌'} {m.name}", f"mod_toggle:{m.id}".encode())]
            if is_on and cls and cls.metadata.settings_schema:
                row.append(Button.inline("⚙️", f"mod_config:{m.id}".encode()))
            rows.append(row)
        rows.append([Button.inline("🔙 بازگشت", b"modules")])
        text = f"🧩 {CATEGORY_NAMES.get(category, category)}\n\nبرای فعال/غیرفعال کردن بزنید:"
        if hasattr(event, "edit"):
            await event.edit(text, buttons=rows)
        else:
            await event.respond(text, buttons=rows)

    async def _toggle_module(self, event, module_id: int) -> None:
        tg_id = event.query.user_id
        from sqlalchemy import select

        from app.database.models.modules import UserModule
        from app.database.models.userbots import Userbot
        from app.modules.manager import ModuleManager

        async with async_session_factory() as session:
            user = await UserService(session).repo.get_by_telegram_id(tg_id)
            if user is None:
                await event.respond(tx.NOT_AUTHORIZED, buttons=kb.back_panel())
                return
            manager = ModuleManager(session)
            um = (
                await session.execute(
                    select(UserModule).where(
                        UserModule.user_id == user.id, UserModule.module_id == module_id
                    )
                )
            ).scalar_one_or_none()
            if um is None or not um.enabled:
                await manager.enable(user.id, module_id)
                action_msg = "فعال شد ✅"
            else:
                await manager.disable(user.id, module_id)
                action_msg = "غیرفعال شد ❌"
            await session.commit()
            # Restart userbot so the module set takes effect immediately.
            ub = (
                await session.execute(
                    select(Userbot).where(Userbot.user_id == user.id).order_by(Userbot.id.desc())
                )
            ).scalars().first()
            if ub is not None:
                await UserbotService(session, self.cipher, self.command_bus).request_restart(
                    ub.id, actor_id=user.id, actor_role="USER"
                )
                await session.commit()
        await event.answer(f"ماژول {action_msg}")
        await self._show_modules(event)

    # ------------------------------------------------------------------ module settings

    async def _show_module_config(self, event, module_id: int) -> None:
        tg_id = event.sender_id if hasattr(event, "sender_id") else event.query.user_id
        from sqlalchemy import select

        from app.database.models.modules import Module, UserModule

        async with async_session_factory() as session:
            user = await UserService(session).repo.get_by_telegram_id(tg_id)
            if user is None:
                await event.respond(tx.NOT_AUTHORIZED, buttons=kb.back_panel())
                return
            module = await session.get(Module, module_id)
            if module is None:
                await event.respond("ماژول یافت نشد.", buttons=kb.back_panel())
                return
            um = (
                await session.execute(
                    select(UserModule).where(
                        UserModule.user_id == user.id, UserModule.module_id == module_id
                    )
                )
            ).scalar_one_or_none()
            if um is None or not um.enabled:
                await event.respond("ابتدا ماژول را فعال کنید.", buttons=kb.back_panel())
                return
            settings = await ModuleManager(session).settings_for(user.id, module_id)
            cls = registry.get(module.key)
            schema = cls.metadata.settings_schema if cls else {}

        rows = []
        for key, spec in schema.items():
            cur = settings.get(key, spec.get("default"))
            stype = spec.get("type", "text")
            if stype == "text":
                rows.append(
                    [Button.inline(f"✏️ {spec.get('label', key)}: {cur}", f"set_text:{um.id}:{key}".encode())]
                )
            elif stype == "choice":
                row = []
                for val, lbl in spec.get("choices", {}).items():
                    mark = "✅ " if cur == val else ""
                    row.append(Button.inline(f"{mark}{lbl}", f"set_choice:{um.id}:{key}:{val}".encode()))
                if row:
                    rows.append(row)
            elif stype == "keywords":
                rows.append([Button.inline(f"➕ افزودن {spec.get('label', key)}", f"kw_add:{um.id}".encode())])
                items = list((cur or {}).items())
                for i, (kw, rep) in enumerate(items):
                    rows.append([Button.inline(f"🗑 {kw} → {rep}", f"kw_del:{um.id}:{i}".encode())])
        rows.append([Button.inline("🔙 بازگشت", b"modules")])
        await event.respond(f"⚙️ تنظیمات {module.name}", buttons=rows)

    async def _ask_setting_text(self, event, um_id: int, key: str) -> None:
        tg_id = event.query.user_id
        await self.state.set(tg_id, "mod_setting", {"um_id": um_id, "key": key})
        await event.respond("✏️ مقدار جدید را بفرست:", buttons=kb.cancel())

    async def _handle_setting_text(self, event, data: dict) -> None:
        tg_id = event.sender_id
        value = (event.message.message or "").strip()
        from app.database.models.modules import UserModule

        async with async_session_factory() as session:
            um = await session.get(UserModule, data["um_id"])
            if um is None:
                await event.respond("خطا: ماژول یافت نشد", buttons=kb.back_panel())
                return
            await ModuleManager(session).set_setting(um.user_id, um.module_id, data["key"], value)
            module_id = um.module_id
            await session.commit()
        await self.state.clear(tg_id)
        await event.respond("✅ ذخیره شد")
        await self._show_module_config(event, module_id)

    async def _save_choice(self, event, um_id: int, key: str, value: str) -> None:
        from app.database.models.modules import UserModule

        async with async_session_factory() as session:
            um = await session.get(UserModule, um_id)
            if um is None:
                await event.respond("خطا: ماژول یافت نشد", buttons=kb.back_panel())
                return
            await ModuleManager(session).set_setting(um.user_id, um.module_id, key, value)
            module_id = um.module_id
            await session.commit()
        await event.answer("✅ ذخیره شد")
        await self._show_module_config(event, module_id)

    async def _ask_keyword(self, event, um_id: int) -> None:
        tg_id = event.query.user_id
        await self.state.set(tg_id, "kw_setting", {"um_id": um_id})
        await event.respond("کلیدواژه و پاسخ را به این شکل بفرست:\n\nکلیدواژه|پاسخ\n\nمثال: سلام|سلام 👋", buttons=kb.cancel())

    async def _handle_keyword(self, event, data: dict) -> None:
        tg_id = event.sender_id
        text = (event.message.message or "").strip()
        if "|" not in text:
            await event.respond("فرمت اشتباه است. مثال: سلام|سلام 👋", buttons=kb.cancel())
            return
        kw, rep = text.split("|", 1)
        kw, rep = kw.strip(), rep.strip()
        from app.database.models.modules import UserModule

        async with async_session_factory() as session:
            um = await session.get(UserModule, data["um_id"])
            if um is None:
                await event.respond("خطا: ماژول یافت نشد", buttons=kb.back_panel())
                return
            manager = ModuleManager(session)
            settings = await manager.settings_for(um.user_id, um.module_id)
            keywords = dict(settings.get("keywords", {}) or {})
            keywords[kw] = rep
            await manager.set_setting(um.user_id, um.module_id, "keywords", keywords)
            module_id = um.module_id
            await session.commit()
        await self.state.clear(tg_id)
        await event.respond("✅ کلیدواژه اضافه شد")
        await self._show_module_config(event, module_id)

    async def _del_keyword(self, event, um_id: int, index: int) -> None:
        from app.database.models.modules import UserModule

        async with async_session_factory() as session:
            um = await session.get(UserModule, um_id)
            if um is None:
                await event.respond("خطا: ماژول یافت نشد", buttons=kb.back_panel())
                return
            manager = ModuleManager(session)
            settings = await manager.settings_for(um.user_id, um.module_id)
            keywords = dict(settings.get("keywords", {}) or {})
            items = list(keywords.items())
            if 0 <= index < len(items):
                keywords.pop(items[index][0], None)
                await manager.set_setting(um.user_id, um.module_id, "keywords", keywords)
            module_id = um.module_id
            await session.commit()
        await event.answer("حذف شد")
        await self._show_module_config(event, module_id)

    # ------------------------------------------------------------------ automation

    async def _show_automation(self, event) -> None:
        tg_id = event.sender_id if hasattr(event, "sender_id") else event.query.user_id
        async with async_session_factory() as session:
            user = await UserService(session).repo.get_by_telegram_id(tg_id)
            if user is None:
                await event.respond(tx.NOT_AUTHORIZED, buttons=kb.back_panel())
                return
            rules = await AutomationRuleRepository(session).list_for_tenant(user.id)
        rows = []
        for r in rules:
            rows.append([Button.inline(f"🗑 {r.name}", f"auto_del:{r.id}".encode())])
        rows.append([Button.inline("➕ ساخت قانون", b"auto_add")])
        rows.append([Button.inline("🔙 بازگشت", b"back_panel")])
        await event.respond("🤖 اتوماسیون\n\nقانون‌های شما (برای حذف بزنید):", buttons=rows)

    async def _ask_auto_condition(self, event) -> None:
        tg_id = event.query.user_id if hasattr(event, "query") else event.sender_id
        await self.state.set(tg_id, "auto_cond", {})
        await event.respond("🔍 کلمه‌ای که اگر در پیام بود... (برای همهٔ پیام‌ها * بفرست):", buttons=kb.cancel())

    async def _handle_auto_cond(self, event, data: dict) -> None:
        tg_id = event.sender_id
        cond = (event.message.message or "").strip()
        await self.state.set(tg_id, "auto_reply", {"cond": cond})
        await event.respond("💬 پاسخ چه باشد؟", buttons=kb.cancel())

    async def _handle_auto_reply(self, event, data: dict) -> None:
        tg_id = event.sender_id
        reply = (event.message.message or "").strip()
        cond = data.get("cond", "")
        from app.database.models.automation import AutomationAction, AutomationCondition, AutomationRule

        async with async_session_factory() as session:
            user = await UserService(session).repo.get_by_telegram_id(tg_id)
            if user is None:
                await event.respond(tx.NOT_AUTHORIZED, buttons=kb.back_panel())
                return
            rule = AutomationRule(
                user_id=user.id,
                name=f"قانون «{cond}»",
                trigger_type="new_message",
                enabled=True,
                priority=100,
            )
            session.add(rule)
            await session.flush()
            if cond and cond != "*":
                session.add(
                    AutomationCondition(
                        rule_id=rule.id, field="text", operator="contains",
                        value={"value": cond}, logic="AND",
                    )
                )
            session.add(
                AutomationAction(
                    rule_id=rule.id, action_type="reply", payload={"text": reply}, sort_order=0
                )
            )
            await session.commit()
        await self.state.clear(tg_id)
        await event.respond("✅ قانون ساخته شد")
        await self._show_automation(event)

    async def _del_rule(self, event, rule_id: int) -> None:
        tg_id = event.query.user_id
        async with async_session_factory() as session:
            user = await UserService(session).repo.get_by_telegram_id(tg_id)
            if user is None:
                await event.respond(tx.NOT_AUTHORIZED, buttons=kb.back_panel())
                return
            rule = await AutomationRuleRepository(session).get_for_tenant(rule_id, user.id)
            await session.delete(rule)
            await session.commit()
        await event.answer("حذف شد")
        await self._show_automation(event)

    # ------------------------------------------------------------------ scheduler

    async def _show_scheduler(self, event) -> None:
        tg_id = event.sender_id if hasattr(event, "sender_id") else event.query.user_id
        async with async_session_factory() as session:
            user = await UserService(session).repo.get_by_telegram_id(tg_id)
            if user is None:
                await event.respond(tx.NOT_AUTHORIZED, buttons=kb.back_panel())
                return
            tasks = await ScheduledTaskRepository(session).list_for_tenant(user.id)
        rows = []
        for t in tasks:
            when = t.next_run_at.strftime("%Y-%m-%d %H:%M") if t.next_run_at else "—"
            rows.append([Button.inline(f"🗑 [{t.status}] {when}", f"sched_del:{t.id}".encode())])
        rows.append([Button.inline("➕ وظیفه جدید", b"sched_add")])
        rows.append([Button.inline("🔙 بازگشت", b"back_panel")])
        await event.respond("⏰ زمان‌بندی\n\nوظیفه‌ها (برای لغو بزنید):", buttons=rows)

    async def _ask_sched_text(self, event) -> None:
        tg_id = event.query.user_id if hasattr(event, "query") else event.sender_id
        await self.state.set(tg_id, "sched_text", {})
        await event.respond("💬 متن پیام را بفرست (به Saved Messages ارسال می‌شود):", buttons=kb.cancel())

    async def _handle_sched_text(self, event, data: dict) -> None:
        tg_id = event.sender_id
        text = (event.message.message or "").strip()
        await self.state.set(tg_id, "sched_time", {"text": text})
        await event.respond(
            "⏰ زمان ارسال را بفرست:\n\nیک‌بار: 2026-08-25 10:00\nروزانه: daily 10:00",
            buttons=kb.cancel(),
        )

    async def _handle_sched_time(self, event, data: dict) -> None:
        tg_id = event.sender_id
        raw = (event.message.message or "").strip()
        text = data.get("text", "")
        try:
            run_at, repeat_rule = self._parse_schedule(raw)
        except ValueError:
            await event.respond("فرمت زمان اشتباه است. مثال: 2026-08-25 10:00", buttons=kb.cancel())
            return
        async with async_session_factory() as session:
            user = await UserService(session).repo.get_by_telegram_id(tg_id)
            if user is None:
                await event.respond(tx.NOT_AUTHORIZED, buttons=kb.back_panel())
                return
            await ScheduledTaskService(session).create(
                user.id, type_="send_message",
                payload={"peer": "me", "text": text},
                run_at=run_at, repeat_rule=repeat_rule,
            )
            await session.commit()
        await self.state.clear(tg_id)
        await event.respond("✅ وظیفه ثبت شد")
        await self._show_scheduler(event)

    async def _del_task(self, event, task_id: int) -> None:
        tg_id = event.query.user_id
        async with async_session_factory() as session:
            user = await UserService(session).repo.get_by_telegram_id(tg_id)
            if user is None:
                await event.respond(tx.NOT_AUTHORIZED, buttons=kb.back_panel())
                return
            await ScheduledTaskService(session).cancel(user.id, task_id)
            await session.commit()
        await event.answer("لغو شد")
        await self._show_scheduler(event)

    @staticmethod
    def _parse_schedule(raw: str) -> tuple:
        from datetime import datetime, timedelta, timezone as tz

        raw = raw.strip()
        local_now = datetime.now().astimezone()
        local_tz = local_now.tzinfo
        if raw.startswith("daily "):
            hhmm = raw[6:].strip()
            t = datetime.strptime(hhmm, "%H:%M").time()
            run_local = datetime.now().astimezone().replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
            if run_local <= local_now:
                run_local += timedelta(days=1)
            return run_local.astimezone(tz.utc), "daily"
        run_local = datetime.strptime(raw, "%Y-%m-%d %H:%M")
        run_local = run_local.replace(tzinfo=local_tz)
        return run_local.astimezone(tz.utc), "one_time"

    # ------------------------------------------------------------------ stats & settings

    async def _show_stats(self, event) -> None:
        tg_id = event.sender_id if hasattr(event, "sender_id") else event.query.user_id
        from sqlalchemy import func, select

        from app.database.models.automation import AutomationRule
        from app.database.models.modules import UserModule
        from app.database.models.scheduler import ScheduledTask
        from app.database.models.userbots import Userbot

        async with async_session_factory() as session:
            user = await UserService(session).repo.get_by_telegram_id(tg_id)
            if user is None:
                await event.respond(tx.NOT_AUTHORIZED, buttons=kb.back_panel())
                return
            modules = await session.scalar(
                select(func.count()).select_from(UserModule).where(
                    UserModule.user_id == user.id, UserModule.enabled.is_(True)
                )
            )
            rules = await session.scalar(
                select(func.count()).select_from(AutomationRule).where(AutomationRule.user_id == user.id)
            )
            tasks = await session.scalar(
                select(func.count()).select_from(ScheduledTask).where(ScheduledTask.user_id == user.id)
            )
            ub = (
                await session.execute(
                    select(Userbot).where(Userbot.user_id == user.id).order_by(Userbot.id.desc())
                )
            ).scalars().first()
            sub = await BillingService(session).subscriptions.active_for_user(user.id)
        ustatus = tx.USERBOT_STATUS_EMOJI.get(ub.status, "—") if ub else "—"
        plan = sub.plan.name if sub else "—"
        text = (
            "📊 آمار\n\n"
            f"🧩 ماژول فعال: {modules}\n"
            f"🤖 قانون اتوماسیون: {rules}\n"
            f"⏰ وظیفه زمان‌بندی: {tasks}\n"
            f"🤖 سلف: {ustatus}\n"
            f"💎 اشتراک: {plan}\n"
        )
        await event.respond(text, buttons=kb.back_panel())

    # ------------------------------------------------------------------ support

    async def _handle_support(self, event, data: dict) -> None:
        tg_id = event.sender_id
        text = (event.message.message or "").strip()
        from app.database.models.support import SupportTicket

        async with async_session_factory() as session:
            user = await UserService(session).get_or_create(
                tg_id,
                username=event.sender.username or None,
                first_name=event.sender.first_name,
            )
            ticket = SupportTicket(user_id=user.id, subject=text[:80], message=text, status="open")
            session.add(ticket)
            await session.commit()
            ticket_id = ticket.id
        await self._notify_owner(
            f"🎫 تیکت جدید #{ticket_id}\nاز: @{user.username or user.id}\n\n{text[:300]}"
        )
        await self.state.clear(tg_id)
        await event.respond(f"✅ پیام شما ثبت شد (تیکت #{ticket_id}).", buttons=kb.main_panel())

    async def _notify_owner(self, text: str) -> None:
        if not self.settings.owner_telegram_id:
            return
        try:
            await self.client.send_message(self.settings.owner_telegram_id, text)
        except Exception as exc:  # noqa: BLE001
            log.error("owner notify failed", extra_fields={"error": str(exc)})

    # ------------------------------------------------------------------ helpers

    async def _send_panel(self, tg_id: int, event, *, edit: bool = False) -> None:
        async with async_session_factory() as session:
            user = await UserService(session).repo.get_by_telegram_id(tg_id)
            account = "فعال" if user and user.is_active and not user.is_suspended else "—"
            plan_name = "—"
            expiry = "—"
            userbot_status = "—"
            if user:
                subs = BillingService(session)
                active = await subs.subscriptions.active_for_user(user.id)
                if active:
                    plan_name = active.plan.name
                    expiry = _fmt(active.expires_at)
                from app.database.models.userbots import Userbot
                from sqlalchemy import select

                ub = (
                    await session.execute(
                        select(Userbot).where(Userbot.user_id == user.id).order_by(Userbot.id.desc())
                    )
                ).scalars().first()
                if ub:
                    userbot_status = tx.USERBOT_STATUS_EMOJI.get(ub.status, ub.status)
        text = tx.MAIN_PANEL.format(account=account, plan=plan_name, expiry=expiry, userbot=userbot_status)
        if edit:
            await event.edit(text, buttons=kb.main_panel())
        else:
            await event.respond(text, buttons=kb.main_panel())

    async def _user_from_event(self, event):
        async with async_session_factory() as session:
            return await UserService(session).get_or_create(
                event.sender_id,
                username=event.sender.username or None,
                first_name=event.sender.first_name,
                last_name=event.sender.last_name,
            )
