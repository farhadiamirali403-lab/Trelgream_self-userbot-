"""Owner/Admin panel inside the central bot (RBAC-gated)."""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from telethon import Button, TelegramClient, events

from app.auth.permissions import Permissions
from app.auth.rbac import admin_has_permission, get_admin_by_telegram_id
from app.billing.service import BillingService
from app.bot.state import ConversationState
from app.core.config import Settings
from app.core.logging import get_logger
from app.core.redis import get_redis
from app.core.security import CommandSigner, SessionCipher
from app.database.models.admins import Admin, AdminRole, Role
from app.database.models.support import SupportTicket
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
        self.state = ConversationState(self.redis)

    def register(self) -> None:
        self.client.add_event_handler(self.on_admin, events.NewMessage(pattern="/admin"))
        self.client.add_event_handler(self.on_admin, events.NewMessage(pattern="/ادمین"))
        self.client.add_event_handler(self.on_callback, events.CallbackQuery())
        self.client.add_event_handler(self.on_admin_message, events.NewMessage(incoming=True))

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
            [Button.inline("👮 مدیران", b"adm_admins")],
            [Button.inline("💳 پلن‌ها", b"adm_plans")],
            [Button.inline("💳 تنظیمات پرداخت", b"adm_pay_settings")],
            [Button.inline("📢 پیام همگانی", b"adm_broadcast")],
            [Button.inline("🎫 پشتیبانی", b"adm_tickets")],
            [Button.inline("🖥 مانیتورینگ", b"adm_monitor")],
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
            elif data == "adm_monitor":
                await self._show_monitor(event, tg_id)
            elif data == "adm_admins":
                await self._show_admins(event, tg_id)
            elif data == "adm_add_admin":
                await self._ask_admin_id(event, tg_id)
            elif data == "cancel_admin":
                await self.state.clear(tg_id)
                await event.respond("لغو شد.")
            elif data.startswith("adm_del_admin:"):
                await self._del_admin(event, tg_id, int(data.split(":", 1)[1]))
            elif data == "adm_tickets":
                await self._show_tickets(event, tg_id)
            elif data.startswith("ticket_reply:"):
                await self._ask_ticket_reply(event, tg_id, int(data.split(":", 1)[1]))
            elif data.startswith("ticket_close:"):
                await self._close_ticket(event, tg_id, int(data.split(":", 1)[1]))
            elif data == "adm_plans":
                await self._show_plans(event, tg_id)
            elif data.startswith("plan_price:"):
                await self._ask_plan_price(event, tg_id, int(data.split(":", 1)[1]))
            elif data == "adm_broadcast":
                await self._ask_broadcast(event, tg_id)
            elif data == "adm_pay_settings":
                await self._show_pay_settings(event, tg_id)
            elif data == "edit_card":
                await self._ask_card(event, tg_id)
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

    # ------------------------------------------------------------------ admins

    async def on_admin_message(self, event) -> None:
        if event.message.message and event.message.message.startswith("/"):
            return
        current = await self.state.get(event.sender_id)
        if current is None:
            return
        state, _ = current
        if state == "awaiting_admin_id":
            await self._handle_admin_id(event)
        elif state == "awaiting_ticket_reply":
            await self._handle_ticket_reply(event)
        elif state == "awaiting_plan_price":
            await self._handle_plan_price(event)
        elif state == "awaiting_broadcast":
            await self._handle_broadcast(event)
        elif state == "awaiting_card":
            await self._handle_card(event)

    async def _show_admins(self, event, tg_id: int) -> None:
        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.ADMINS_MANAGE):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            admins = (await session.execute(select(Admin).order_by(Admin.id))).scalars().all()
        rows = []
        for a in admins:
            roles = ", ".join(r.name for r in a.roles) or "—"
            rows.append([Button.inline(f"🗑 {a.telegram_id} — {roles}", f"adm_del_admin:{a.id}".encode())])
        rows.append([Button.inline("➕ افزودن ادمین", b"adm_add_admin")])
        await event.respond("👮 مدیران\n\nبرای حذف روی هر ادمین بزنید:", buttons=rows)

    async def _ask_admin_id(self, event, tg_id: int) -> None:
        await self.state.set(tg_id, "awaiting_admin_id", {})
        await event.respond(
            "شناسه عددی تلگرام ادمین جدید را بفرست (مثلاً 123456789):",
            buttons=[[Button.inline("❌ لغو", b"cancel_admin")]],
        )

    async def _handle_admin_id(self, event) -> None:
        tg_id = event.sender_id
        raw = (event.message.message or "").strip()
        try:
            admin_tg = int(raw)
        except ValueError:
            await event.respond("شناسه نامعتبر است؛ عدد بفرست.", buttons=[[Button.inline("❌ لغو", b"cancel_admin")]])
            return
        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.ADMINS_MANAGE):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            existing = (
                await session.execute(select(Admin).where(Admin.telegram_id == str(admin_tg)))
            ).scalar_one_or_none()
            if existing is not None:
                await self.state.clear(tg_id)
                await event.respond("این شناسه قبلاً ادمین است.")
                return
            admin = Admin(telegram_id=str(admin_tg), name="", is_active=True)
            session.add(admin)
            await session.flush()
            admin_role = (await session.execute(select(Role).where(Role.name == "ADMIN"))).scalar_one()
            session.add(AdminRole(admin_id=admin.id, role_id=admin_role.id))
            await session.commit()
        await self.state.clear(tg_id)
        await event.respond(f"✅ ادمین {admin_tg} با نقش ADMIN اضافه شد.")
        await self._show_admins(event, tg_id)

    async def _del_admin(self, event, tg_id: int, admin_id: int) -> None:
        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.ADMINS_MANAGE):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            admin = await session.get(Admin, admin_id)
            if admin is None:
                await event.answer("یافت نشد")
                return
            if self.settings.owner_telegram_id and admin.telegram_id == str(self.settings.owner_telegram_id):
                await event.answer("Owner قابل حذف نیست")
                return
            await session.delete(admin)
            await session.commit()
        await event.answer("حذف شد")
        await self._show_admins(event, tg_id)

    # ------------------------------------------------------------------ support tickets

    async def _show_tickets(self, event, tg_id: int) -> None:
        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.SUPPORT_MANAGE):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            tickets = (
                await session.execute(
                    select(SupportTicket)
                    .where(SupportTicket.status == "open")
                    .order_by(SupportTicket.id.desc())
                    .limit(20)
                )
            ).scalars().all()
        if not tickets:
            await event.respond("تیکت بازی وجود ندارد.")
            return
        for t in tickets:
            await event.respond(
                f"🎫 تیکت #{t.id} — کاربر {t.user_id}\n\n{t.message[:300]}",
                buttons=[
                    [
                        Button.inline("💬 پاسخ", f"ticket_reply:{t.id}".encode()),
                        Button.inline("✅ بستن", f"ticket_close:{t.id}".encode()),
                    ]
                ],
            )

    async def _ask_ticket_reply(self, event, tg_id: int, ticket_id: int) -> None:
        await self.state.set(tg_id, "awaiting_ticket_reply", {"ticket_id": ticket_id})
        await event.respond(
            "💬 متن پاسخ را بنویسید (برای کاربر ارسال می‌شود):",
            buttons=[[Button.inline("❌ لغو", b"cancel_admin")]],
        )

    async def _handle_ticket_reply(self, event) -> None:
        tg_id = event.sender_id
        reply_text = (event.message.message or "").strip()
        if not reply_text:
            await event.respond("پاسخ خالی است.", buttons=[[Button.inline("❌ لغو", b"cancel_admin")]])
            return
        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.SUPPORT_MANAGE):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            current = await self.state.get(tg_id)
            ticket_id = (current[1] if current else {}).get("ticket_id") if current else None
            if ticket_id is None:
                await event.respond("خطا در دریافت تیکت.")
                return
            ticket = await session.get(SupportTicket, ticket_id)
            if ticket is None:
                await event.respond("تیکت یافت نشد.")
                return
            from app.database.models.users import User as _User

            user = await session.get(_User, ticket.user_id)
            if user is not None:
                try:
                    await self.client.send_message(
                        user.telegram_id, f"📩 پاسخ پشتیبانی (تیکت #{ticket.id}):\n\n{reply_text}"
                    )
                except Exception as exc:  # noqa: BLE001
                    log.warning("ticket reply send failed", extra_fields={"error": str(exc)})
            ticket.status = "answered"
            await session.commit()
        await self.state.clear(tg_id)
        await event.respond("✅ پاسخ ارسال شد و تیکت به‌عنوان پاسخ‌داده‌شده علامت خورد.")

    async def _close_ticket(self, event, tg_id: int, ticket_id: int) -> None:
        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.SUPPORT_MANAGE):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            ticket = await session.get(SupportTicket, ticket_id)
            if ticket is not None:
                ticket.status = "closed"
                await session.commit()
        await event.answer("بسته شد")

    # ------------------------------------------------------------------ plans

    async def _show_plans(self, event, tg_id: int) -> None:
        from app.database.models.billing import Plan

        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.SETTINGS_EDIT):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            plans = (await session.execute(select(Plan).order_by(Plan.sort_order))).scalars().all()
        rows = []
        for p in plans:
            rows.append(
                [Button.inline(f"✏️ {p.name} — {p.price:,} تومان / {p.duration_days} روز", f"plan_price:{p.id}".encode())]
            )
        await event.respond("💳 پلن‌ها\n\nبرای ویرایش قیمت روی هر پلن بزنید:", buttons=rows)

    async def _ask_plan_price(self, event, tg_id: int, plan_id: int) -> None:
        await self.state.set(tg_id, "awaiting_plan_price", {"plan_id": plan_id})
        await event.respond(
            "قیمت جدید (تومان) و مدت (روز) را به این شکل بفرست:\n\nقیمت|مدت\n\nمثال: 500000|30",
            buttons=[[Button.inline("❌ لغو", b"cancel_admin")]],
        )

    async def _handle_plan_price(self, event) -> None:
        tg_id = event.sender_id
        raw = (event.message.message or "").strip()
        if "|" not in raw:
            await event.respond("فرمت اشتباه است. مثال: 500000|30", buttons=[[Button.inline("❌ لغو", b"cancel_admin")]])
            return
        try:
            price_str, days_str = raw.split("|", 1)
            price = int(price_str.strip().replace(",", ""))
            days = int(days_str.strip())
        except ValueError:
            await event.respond("عدد نامعتبر است.", buttons=[[Button.inline("❌ لغو", b"cancel_admin")]])
            return
        from app.database.models.billing import Plan

        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.SETTINGS_EDIT):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            current = await self.state.get(tg_id)
            plan_id = (current[1] if current else {}).get("plan_id") if current else None
            if plan_id is None:
                await event.respond("خطا در دریافت پلن.")
                return
            plan = await session.get(Plan, plan_id)
            if plan is None:
                await event.respond("پلن یافت نشد.")
                return
            plan.price = price
            plan.duration_days = days
            await session.commit()
        await self.state.clear(tg_id)
        await event.respond(f"✅ قیمت {price:,} تومان و مدت {days} روز ذخیره شد.")
        await self._show_plans(event, tg_id)

    # ------------------------------------------------------------------ broadcast

    async def _ask_broadcast(self, event, tg_id: int) -> None:
        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.BROADCAST_SEND):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
        await self.state.set(tg_id, "awaiting_broadcast", {})
        await event.respond(
            "📢 متن پیام همگانی را بفرستید (برای همهٔ کاربران ارسال می‌شود):",
            buttons=[[Button.inline("❌ لغو", b"cancel_admin")]],
        )

    async def _handle_broadcast(self, event) -> None:
        tg_id = event.sender_id
        text = (event.message.message or "").strip()
        if not text:
            await event.respond("پیام خالی است.", buttons=[[Button.inline("❌ لغو", b"cancel_admin")]])
            return
        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.BROADCAST_SEND):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            users = (
                await session.execute(select(User).where(User.is_active.is_(True)))
            ).scalars().all()
            target_ids = [u.telegram_id for u in users]
        await self.state.clear(tg_id)
        await event.respond(f"📢 در حال ارسال به {len(target_ids)} کاربر...")

        ok = 0
        fail = 0
        for tid in target_ids:
            try:
                await self.client.send_message(tid, f"📢 اطلاعیه:\n\n{text}")
                ok += 1
            except Exception as exc:  # noqa: BLE001
                log.warning("broadcast send failed", extra_fields={"tg": tid, "error": str(exc)})
                fail += 1
            await asyncio.sleep(0.3)
        await event.respond(f"✅ ارسال همگانی تمام شد:\nموفق: {ok}\nناموفق: {fail}")

    # ------------------------------------------------------------------ payment settings

    async def _show_pay_settings(self, event, tg_id: int) -> None:
        from app.database.models.settings import PaymentSetting

        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.SETTINGS_EDIT):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            ps = (await session.execute(select(PaymentSetting).order_by(PaymentSetting.id))).scalars().first()
            if ps is None:
                ps = PaymentSetting(card_number="", card_owner="", is_active=True)
                session.add(ps)
                await session.commit()
        await event.respond(
            "💳 تنظیمات پرداخت\n\n"
            f"شماره کارت: {ps.card_number or '—'}\n"
            f"صاحب کارت: {ps.card_owner or '—'}\n",
            buttons=[[Button.inline("✏️ ویرایش کارت", b"edit_card")]],
        )

    async def _ask_card(self, event, tg_id: int) -> None:
        await self.state.set(tg_id, "awaiting_card", {})
        await event.respond(
            "شماره کارت و نام صاحب کارت را به این شکل بفرست:\n\nشماره|نام\n\nمثال: 6037991234567890|رضا فرهادی",
            buttons=[[Button.inline("❌ لغو", b"cancel_admin")]],
        )

    async def _handle_card(self, event) -> None:
        tg_id = event.sender_id
        raw = (event.message.message or "").strip()
        if "|" not in raw:
            await event.respond("فرمت اشتباه است. مثال: 6037991234567890|رضا فرهادی", buttons=[[Button.inline("❌ لغو", b"cancel_admin")]])
            return
        card, owner = raw.split("|", 1)
        card, owner = card.strip(), owner.strip()
        from app.database.models.settings import PaymentSetting

        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.SETTINGS_EDIT):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            ps = (await session.execute(select(PaymentSetting).order_by(PaymentSetting.id))).scalars().first()
            if ps is None:
                ps = PaymentSetting(card_number=card, card_owner=owner, is_active=True)
                session.add(ps)
            else:
                ps.card_number = card
                ps.card_owner = owner
            await session.commit()
        await self.state.clear(tg_id)
        await event.respond("✅ تنظیمات پرداخت ذخیره شد.")
        await self._show_pay_settings(event, tg_id)

    # ------------------------------------------------------------------ monitoring

    async def _show_monitor(self, event, tg_id: int) -> None:
        import psutil
        from sqlalchemy import func

        from app.database.models.workers import Worker
        from app.scheduler.queue import TASK_QUEUE
        from app.workers.commands import COMMAND_QUEUE

        async with async_session_factory() as session:
            if not await self._require(session, tg_id, Permissions.LOGS_VIEW):
                await event.respond("⛔️ دسترسی مجاز نیست.")
                return
            workers = (await session.execute(select(Worker).order_by(Worker.id))).scalars().all()
            online = await session.scalar(
                select(func.count()).select_from(Userbot).where(Userbot.status == "RUNNING")
            )
            total = await session.scalar(select(func.count()).select_from(Userbot))

        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        try:
            cmd_q = await self.redis.llen(COMMAND_QUEUE)
            task_q = await self.redis.llen(TASK_QUEUE)
        except Exception:  # noqa: BLE001
            cmd_q = task_q = "—"

        lines = [
            "🖥 مانیتورینگ",
            "━━━━━━━━━━━━━━━",
            f"🧠 CPU: {cpu}%",
            f"💾 RAM: {ram.percent}% ({ram.used // (1024**2)}MB از {ram.total // (1024**2)}MB)",
            f"🤖 سلف آنلاین: {online or 0} از {total or 0}",
            f"📥 صف دستورات: {cmd_q}",
            f"📤 صف وظایف: {task_q}",
            "",
            "👷 ورکرها:",
        ]
        for w in workers:
            lines.append(f"  • {w.name}: {w.status} (load={w.load})")
        await event.respond("\n".join(lines))
