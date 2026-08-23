"""Central Telegram bot: Persian UI, auth flow, billing, panel."""

from __future__ import annotations

from datetime import datetime, timezone

from telethon import TelegramClient, events

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
        await self.client.start(bot_token=self.settings.central_bot_token)
        log.info("Central bot started", extra_fields={"username": (await self.client.get_me()).username})
        await self.client.run_until_disconnected()

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
        await event.respond(tx.SETTINGS_INFO, buttons=kb.back_panel())

    async def on_support(self, event) -> None:
        await event.respond(tx.SUPPORT_INFO, buttons=kb.back_panel())

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
        elif data in ("settings", "support", "modules", "automation", "scheduler", "stats"):
            await event.respond("این بخش در حال توسعه است.", buttons=kb.back_panel())
        else:
            await self._send_panel(tg_id, event, edit=True)

    # ------------------------------------------------------------------ auth flow

    async def _start_auth(self, event) -> None:
        tg_id = event.sender_id if hasattr(event, "sender_id") else event.query.user_id
        await self.state.set(tg_id, "awaiting_phone")
        await event.respond(tx.ASK_PHONE, buttons=kb.cancel())

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
