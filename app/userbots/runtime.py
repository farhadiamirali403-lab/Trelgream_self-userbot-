"""Per-userbot runtime: Telethon client + enabled modules + built-in panel."""

from __future__ import annotations

from telethon import Button, TelegramClient, events

from app.core.exceptions import SessionError
from app.modules.base import BaseModule, ModuleContext
from app.modules.registry import ModuleRegistry

_EVENT_BUILDERS = {
    "new_message": events.NewMessage,
    "edited_message": events.MessageEdited,
    "deleted_message": events.MessageDeleted,
}


class UserbotRuntime:
    """Owns a single userbot's client, module instances and management panel."""

    def __init__(
        self,
        *,
        user_id: int,
        userbot_id: int,
        client: TelegramClient,
        registry: ModuleRegistry,
        module_classes: list[type[BaseModule]],
        module_settings: dict[str, dict],
        command_bus=None,
    ) -> None:
        self.user_id = user_id
        self.userbot_id = userbot_id
        self.client = client
        self.registry = registry
        self.module_classes = module_classes
        self.module_settings = module_settings
        self.command_bus = command_bus
        self.modules: list[BaseModule] = []

    async def start(self) -> None:
        await self.client.connect()
        if not await self.client.is_user_authorized():
            raise SessionError("نشست تلگرام نامعتبر است")
        for module_cls in self.module_classes:
            ctx = ModuleContext(
                user_id=self.user_id,
                userbot_id=self.userbot_id,
                client=self.client,
                settings=self.module_settings.get(module_cls.metadata.key, {}),
            )
            module = module_cls(ctx)
            self.modules.append(module)
            for spec in module_cls.handlers():
                builder = _EVENT_BUILDERS.get(spec.event_type)
                if builder is None:
                    continue
                kwargs: dict = {"incoming": spec.incoming, "outgoing": spec.outgoing}
                if spec.pattern:
                    kwargs["pattern"] = spec.pattern
                    # دستورات باید به پیام‌های خودِ کاربر هم پاسخ بدهند (outgoing).
                    kwargs["outgoing"] = True
                self.client.add_event_handler(spec.func.__get__(module), builder(**kwargs))
        for module in self.modules:
            await module.on_start()

        # Built-in management panel: /panel در هر چت (پی‌وی، سِیو مسیج، گروه).
        self.client.add_event_handler(
            self._handle_panel, events.NewMessage(pattern=r"^/panel", incoming=True)
        )
        self.client.add_event_handler(
            self._handle_panel, events.NewMessage(pattern=r"^/panel", outgoing=True)
        )
        # Help: راهنمای همهٔ دستورات ماژول‌های فعال.
        self.client.add_event_handler(
            self._handle_help, events.NewMessage(pattern=r"^/help", incoming=True)
        )
        self.client.add_event_handler(
            self._handle_help, events.NewMessage(pattern=r"^/help", outgoing=True)
        )
        self.client.add_event_handler(self._handle_panel_callback, events.CallbackQuery())

    async def _handle_help(self, event) -> None:
        try:
            await event.reply(self._build_help_text())
        except Exception:  # noqa: BLE001
            pass

    def _build_help_text(self) -> str:
        import re
        from collections import defaultdict

        from app.modules.builtin.catalog import CATEGORY_NAMES

        by_cat: dict = defaultdict(list)
        for cls in self.registry.all():
            if cls.metadata.not_implemented:
                continue
            cmds = []
            for spec in cls.handlers():
                m = re.search(r"\^/(\w+)", spec.pattern or "")
                if m:
                    cmds.append("/" + m.group(1))
            if cmds:
                by_cat[cls.metadata.category].append((cls.metadata.name, cmds))
        lines = ["━━━━━━━━━━━━━━━\n📖 راهنمای دستورات سلف\n━━━━━━━━━━━━━━━"]
        for cat in sorted(by_cat):
            lines.append(f"\n{CATEGORY_NAMES.get(cat, cat)}:")
            for name, cmds in by_cat[cat]:
                lines.append(f"  • {name}: {'، '.join(cmds)}")
        lines.append("\nبرای مدیریت ماژول‌ها: /panel")
        return "\n".join(lines)

    # ------------------------------------------------------------------ panel

    async def _handle_panel(self, event) -> None:
        text, buttons = await self._panel_content()
        try:
            await event.reply(text, buttons=buttons)
        except Exception:  # noqa: BLE001
            pass

    async def _panel_content(self) -> tuple[str, list]:
        async with self._session() as session:
            plan, modules_count, rules, tasks = await self._load_stats(session)
        text = (
            "━━━━━━━━━━━━━━━\n"
            "🤖 پنل سلف\n"
            "━━━━━━━━━━━━━━━\n\n"
            f"💎 اشتراک: {plan}\n"
            f"🧩 ماژول فعال: {modules_count}\n"
            f"🤖 قانون اتوماسیون: {rules}\n"
            f"⏰ وظیفه زمان‌بندی: {tasks}\n"
            "🟢 وضعیت: آنلاین\n"
        )
        buttons = [
            [Button.inline("🧩 قابلیت‌ها", b"ub_modules"), Button.inline("📊 آمار", b"ub_stats")],
            [Button.inline("📖 راهنما", b"ub_help"), Button.inline("🔗 ربات مرکزی", b"ub_central")],
        ]
        return text, buttons

    async def _handle_panel_callback(self, event) -> None:
        # مدیریت فقط برای صاحب حساب (خودِ کاربر).
        try:
            me = await self.client.get_me()
        except Exception:  # noqa: BLE001
            return
        if event.query.user_id != me.id:
            await event.answer("فقط صاحب حساب می‌تواند مدیریت کند.")
            return
        data = event.data.decode()
        await event.answer()
        if data == "ub_modules":
            await self._show_categories(event)
        elif data == "ub_back":
            text, buttons = await self._panel_content()
            await event.edit(text, buttons=buttons)
        elif data.startswith("ub_cat:"):
            await self._show_category(event, data.split(":", 1)[1])
        elif data.startswith("ub_toggle:"):
            await self._toggle_module(event, int(data.split(":", 1)[1]))
        elif data == "ub_stats":
            await self._show_stats(event)
        elif data == "ub_help":
            await event.edit(self._build_help_text(), buttons=[[Button.inline("🔙 بازگشت", b"ub_back")]])
        elif data == "ub_central":
            await event.respond("برای مدیریت کامل به ربات مرکزی /start بزنید.")
        elif data.startswith("ub_ni:"):
            await event.answer("⏳ این قابلیت هنوز پیاده‌سازی نشده است (NOT IMPLEMENTED)")

    async def _show_categories(self, event) -> None:
        from collections import defaultdict

        from app.modules.builtin.catalog import CATEGORY_NAMES

        counts: dict = defaultdict(int)
        for cls in self.registry.all():
            counts[cls.metadata.category] += 1
        rows = []
        for cat, name in CATEGORY_NAMES.items():
            if counts.get(cat, 0):
                rows.append([Button.inline(f"{name} ({counts[cat]})", f"ub_cat:{cat}".encode())])
        rows.append([Button.inline("🔙 بازگشت", b"ub_back")])
        await event.edit("🧩 قابلیت‌ها\n\nیک دسته را انتخاب کنید:", buttons=rows)

    async def _show_category(self, event, category: str) -> None:
        from sqlalchemy import select

        from app.database.models.modules import Module, UserModule
        from app.modules.builtin.catalog import CATEGORY_NAMES

        async with self._session() as session:
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
                            UserModule.user_id == self.user_id, UserModule.enabled.is_(True)
                        )
                    )
                ).scalars().all()
            }
        rows = []
        for m in modules:
            cls = self.registry.get(m.key)
            not_impl = cls.metadata.not_implemented if cls else False
            if not_impl:
                rows.append([Button.inline(f"⏳ {m.name}", f"ub_ni:{m.id}".encode())])
                continue
            prefix = "✅" if m.id in enabled_ids else "❌"
            rows.append([Button.inline(f"{prefix} {m.name}", f"ub_toggle:{m.id}".encode())])
        rows.append([Button.inline("🔙 بازگشت", b"ub_modules")])
        await event.edit(
            f"🧩 {CATEGORY_NAMES.get(category, category)}\n\nبرای فعال/غیرفعال کردن بزنید:",
            buttons=rows,
        )

    async def _toggle_module(self, event, module_id: int) -> None:
        from sqlalchemy import select

        from app.database.models.modules import UserModule
        from app.modules.manager import ModuleManager

        async with self._session() as session:
            um = (
                await session.execute(
                    select(UserModule).where(
                        UserModule.user_id == self.user_id, UserModule.module_id == module_id
                    )
                )
            ).scalar_one_or_none()
            manager = ModuleManager(session)
            if um is None or not um.enabled:
                await manager.enable(self.user_id, module_id)
                msg = "فعال شد ✅"
            else:
                await manager.disable(self.user_id, module_id)
                msg = "غیرفعال شد ❌"
            await session.commit()
            # Request restart so the change takes effect.
            if self.command_bus is not None:
                await self.command_bus.send(
                    "restart", self.userbot_id, actor_id=self.user_id, actor_role="USER"
                )
        await event.answer(f"ماژول {msg} — سلف در حال راه‌اندازی مجدد است...")

    async def _show_stats(self, event) -> None:
        async with self._session() as session:
            plan, modules_count, rules, tasks = await self._load_stats(session)
        text = (
            "📊 آمار\n\n"
            f"💎 اشتراک: {plan}\n"
            f"🧩 ماژول فعال: {modules_count}\n"
            f"🤖 قانون اتوماسیون: {rules}\n"
            f"⏰ وظیفه زمان‌بندی: {tasks}\n"
            "🟢 وضعیت: آنلاین\n"
        )
        await event.edit(text, buttons=[[Button.inline("🔙 بازگشت", b"ub_back")]])

    # ------------------------------------------------------------------ helpers

    def _session(self):
        from app.database.session import async_session_factory

        return async_session_factory()

    async def _load_stats(self, session) -> tuple:
        from sqlalchemy import func, select

        from app.billing.service import BillingService
        from app.database.models.automation import AutomationRule
        from app.database.models.modules import UserModule
        from app.database.models.scheduler import ScheduledTask

        sub = await BillingService(session).subscriptions.active_for_user(self.user_id)
        plan = sub.plan.name if sub and sub.plan else "—"
        modules_count = await session.scalar(
            select(func.count())
            .select_from(UserModule)
            .where(UserModule.user_id == self.user_id, UserModule.enabled.is_(True))
        )
        rules = await session.scalar(
            select(func.count()).select_from(AutomationRule).where(AutomationRule.user_id == self.user_id)
        )
        tasks = await session.scalar(
            select(func.count()).select_from(ScheduledTask).where(ScheduledTask.user_id == self.user_id)
        )
        return plan, modules_count or 0, rules or 0, tasks or 0

    async def stop(self) -> None:
        for module in self.modules:
            await module.on_stop()
        await self.client.disconnect()
