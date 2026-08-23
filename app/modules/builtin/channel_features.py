"""Channel features: scheduled posts and post templates."""

from __future__ import annotations

from app.modules.base import BaseModule, ModuleMetadata, handler


def _parse_schedule(raw: str):
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


class ScheduledPostsModule(BaseModule):
    metadata = ModuleMetadata(
        key="scheduled_posts", name="پست زمان‌بندی", category="channels",
        description="زمان‌بندی پست کانال با /post زمان | متن",
    )

    @handler("new_message", pattern=r"^/post")
    async def on_post(self, event) -> None:
        raw = (event.message.message or "")[5:].strip()
        if "|" not in raw:
            await event.reply("استفاده: /post زمان | متن\nمثال: /post daily 10:00 | سلام")
            return
        schedule, text = raw.split("|", 1)
        schedule, text = schedule.strip(), text.strip()
        try:
            run_at, repeat = _parse_schedule(schedule)
        except ValueError:
            await event.reply("زمان نامعتبر است. مثال: 2026-08-25 10:00 یا daily 10:00")
            return
        from app.database.session import async_session_factory
        from app.scheduler.service import ScheduledTaskService

        async with async_session_factory() as session:
            await ScheduledTaskService(session).create(
                self.context.user_id,
                type_="send_message",
                payload={"peer": event.chat_id, "text": text},
                run_at=run_at,
                repeat_rule=repeat,
            )
            await session.commit()
        await event.reply(f"✅ پست زمان‌بندی شد ({repeat}).")


class PostTemplatesModule(BaseModule):
    metadata = ModuleMetadata(
        key="post_templates", name="قالب پست", category="channels",
        description="ذخیره و استفاده از قالب پست با /tmpl",
    )

    @handler("new_message", pattern=r"^/tmpl")
    async def on_tmpl(self, event) -> None:
        raw = (event.message.message or "")[5:].strip()
        templates = dict(self.setting("templates", {}) or {})
        if not raw:
            await event.reply("استفاده:\n/tmpl نام | متن (ذخیره)\n/tmpl نام (ارسال)")
            return
        if "|" in raw:
            name, text = raw.split("|", 1)
            name, text = name.strip(), text.strip()
            templates[name] = text
            await self.persist_setting("templates", templates)
            await event.reply(f"✅ قالب «{name}» ذخیره شد.")
        else:
            name = raw.strip()
            text = templates.get(name)
            if text is None:
                await event.reply("قالبی با این نام یافت نشد.")
            else:
                await event.reply(text)
