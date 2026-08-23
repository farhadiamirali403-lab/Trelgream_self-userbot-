"""Owner/Admin panel inside the central bot (RBAC-gated)."""

from __future__ import annotations

from telethon import Button, TelegramClient, events

from app.auth.permissions import Permissions
from app.auth.rbac import admin_has_permission, get_admin_by_telegram_id
from app.billing.service import BillingService
from app.core.config import Settings
from app.core.logging import get_logger
from app.core.redis import get_redis
from app.core.security import CommandSigner, SessionCipher
from app.database.models.userbots import Userbot
from app.database.models.users import User
from app.database.session import async_session_factory
from app.userbots.service import UserbotService
from app.workers.commands import CommandBus

log = get_logger("bot.admin")

ADMIN_PANEL = "👑 پنل Owner\n\nبرای مدیریت از گزینه‌های زیر استفاده کنید."


class AdminPanel:
    def __init__(self, settings: Settings, client: TelegramClient) -> None:
        self.settings = settings
        self.client = client
        self.redis = get_redis()
        self.cipher = SessionCipher(settings.session_encryption_key)
        self.command_bus = CommandBus(self.redis, CommandSigner(settings.session_encryption_key or "cmd"))

    def register(self) -> None:
        self.client.add_event_handler(self.on_admin, events.NewMessage(pattern="/admin"))
        self.client.add_event_handler(self.on_callback, events.CallbackQuery())

    # ------------------------------------------------------------------ auth

    async def _resolve(self, tg_id: int, session) -> tuple[str, int] | None:
        """Return (role, admin_id) if the user is an admin, else None."""
        if self.settings.owner_telegram_id and tg_id == self.settings.owner_telegram_id:
            admin = await get_admin_by_telegram_id(session, tg_id)
            return ("OWNER", admin.id if admin else 0)
        admin = await get_admin_by_telegram_id(session, tg_id)
        if admin is None or not admin.is_active:
            return None
        return ("ADMIN", admin.id)

    async def _require(self, session, tg_id: int, permission: str) -> tuple[str, int] | None:
        resolved = await self._resolve(tg_id, session)
        if resolved is None:
            return None
        role, admin_id = resolved
        if role == "OWNER":
            return resolved
        if await admin_has_permission(session, admin_id, permission):
            return resolved
        return None

    # ------------------------------------------------------------------ handlers

    async def on_admin(self, event) -> None:
        async with async_session_factory() as session:
            resolved = await self._resolve(event.sender_id, session)
            if resolved is None:
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            role, _ = resolved
        buttons = [
            [Button.inline("💰 پرداخت‌های در انتظار", b"adm_payments")],
            [Button.inline("🤖 Userbotها", b"adm_userbots")],
            [Button.inline("👥 کاربران", b"adm_users")],
            [Button.inline("📊 آمار", b"adm_stats")],
        ]
        await event.respond(f"👑 پنل {role}\n\nاز گزینه‌ها استفاده کنید.", buttons=buttons)

    async def on_callback(self, event) -> None:
        data = event.data.decode()
        tg_id = event.query.user_id
        await event.answer()
        try:
            if data == "adm_payments":
                await self._payments(event, tg_id)
            elif data == "adm_userbots":
                await self._userbots(event, tg_id)
            elif data == "adm_users":
                await self._users(event, tg_id)
            elif data == "adm_stats":
                await self._stats(event, tg_id)
            elif data.startswith("approve:"):
                await self._approve(event, tg_id, int(data.split(":", 1)[1]))
            elif data.startswith("reject:"):
                await self._reject(event, tg_id, int(data.split(":", 1)[1]))
            elif data.startswith("ub_start:"):
                await self._ub_action(event, tg_id, int(data.split(":", 1)[1]), "start")
            elif data.startswith("ub_stop:"):
                await self._ub_action(event, tg_id, int(data.split(":", 1)[1]), "stop")
        except Exception as exc:  # noqa: BLE001
            log.error("admin callback failed", extra_fields={"error": str(exc)})
            await event.respond(f"⚠️ خطا: {exc}")

    async def _payments(self, event, tg_id: int) -> None:
        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.PAYMENTS_VIEW):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            payments = await BillingService(session).pending_payments()
            if not payments:
                await event.respond("هیچ پرداخت در انتظاری وجود ندارد.")
                return
            for p in payments:
                text = (
                    f"💰 پرداخت در انتظار\n\n"
                    f"شناسه: {p.reference}\n"
                    f"کاربر: {p.user_id}\n"
                    f"مبلغ: {p.amount:,} تومان\n"
                )
                buttons = [
                    [Button.inline("✅ تأیید", f"approve:{p.id}".encode())],
                    [Button.inline("❌ رد", f"reject:{p.id}".encode())],
                ]
                await event.respond(text, buttons=buttons)

    async def _approve(self, event, tg_id: int, payment_id: int) -> None:
        async with async_session_factory() as session:
            resolved = await self._require(session, tg_id, Permissions.PAYMENTS_APPROVE)
            if resolved is None:
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            role, admin_id = resolved
            payment = await BillingService(session).approve_payment(
                payment_id, admin_id=admin_id, admin_role=role
            )
            await session.commit()
            await event.respond(f"✅ پرداخت {payment.reference} تأیید شد.")

    async def _reject(self, event, tg_id: int, payment_id: int) -> None:
        async with async_session_factory() as session:
            resolved = await self._require(session, tg_id, Permissions.PAYMENTS_REJECT)
            if resolved is None:
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            role, admin_id = resolved
            payment = await BillingService(session).reject_payment(
                payment_id, admin_id=admin_id, admin_role=role
            )
            await session.commit()
            await event.respond(f"❌ پرداخت {payment.reference} رد شد.")

    async def _userbots(self, event, tg_id: int) -> None:
        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.USERBOTS_VIEW):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            from sqlalchemy import func, select

            online = await session.scalar(select(func.count()).select_from(Userbot).where(Userbot.status == "RUNNING"))
            total = await session.scalar(select(func.count()).select_from(Userbot))
            userbots = (await session.execute(select(Userbot).order_by(Userbot.id.desc()).limit(20))).scalars().all()
            lines = [f"🤖 Userbotها\n\n🟢 آنلاین: {online} از {total}\n"]
            for ub in userbots:
                lines.append(f"#{ub.id} — {ub.status}")
            for ub in userbots[:10]:
                buttons = [
                    [
                        Button.inline("▶️", f"ub_start:{ub.id}".encode()),
                        Button.inline("⏹", f"ub_stop:{ub.id}".encode()),
                    ]
                ]
                await event.respond(f"Userbot #{ub.id} — {ub.status}", buttons=buttons)
            await event.respond("\n".join(lines))

    async def _users(self, event, tg_id: int) -> None:
        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.USERS_VIEW):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            from sqlalchemy import func, select

            total = await session.scalar(select(func.count()).select_from(User))
            await event.respond(f"👥 کاربران\n\nتعداد کل: {total}")

    async def _stats(self, event, tg_id: int) -> None:
        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.USERS_VIEW):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            from sqlalchemy import func, select

            users = await session.scalar(select(func.count()).select_from(User))
            online = await session.scalar(select(func.count()).select_from(Userbot).where(Userbot.status == "RUNNING"))
            await event.respond(f"📊 آمار\n\n👥 کاربران: {users}\n🤖 سلف آنلاین: {online}")

    async def _ub_action(self, event, tg_id: int, userbot_id: int, action: str) -> None:
        async with async_session_factory() as session:
            perm = Permissions.USERBOTS_START if action == "start" else Permissions.USERBOTS_STOP
            resolved = await self._require(session, tg_id, perm)
            if resolved is None:
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            role, admin_id = resolved
            service = UserbotService(session, self.cipher, self.command_bus)
            if action == "start":
                await service.request_start(userbot_id, actor_id=admin_id, actor_role=role)
            else:
                await service.request_stop(userbot_id, actor_id=admin_id, actor_role=role)
            await session.commit()
            await event.respond(f"✅ دستور {action} برای Userbot #{userbot_id} ارسال شد.")
