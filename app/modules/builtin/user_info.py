"""User info module: show user info via /info (or reply)."""

from __future__ import annotations

from app.modules.base import BaseModule, ModuleMetadata, handler


class UserInfoModule(BaseModule):
    metadata = ModuleMetadata(
        key="user_info",
        name="اطلاعات کاربر",
        category="search",
        description="نمایش اطلاعات کاربر با دستور /info (یا ریپلای روی پیام کاربر)",
        permission="module.user_info.use",
    )

    @handler("new_message", pattern=r"^/info")
    async def on_info(self, event) -> None:
        user = event.sender
        try:
            if event.message.is_reply:
                replied = await event.message.get_reply_message()
                if replied is not None and replied.sender is not None:
                    user = replied.sender
        except Exception:  # noqa: BLE001
            pass
        if user is None:
            await event.reply("کاربری یافت نشد.")
            return
        name = f"{getattr(user, 'first_name', '') or ''} {getattr(user, 'last_name', '') or ''}".strip()
        text = (
            "👤 اطلاعات کاربر\n\n"
            f"ID: {user.id}\n"
            f"نام: {name}\n"
            f"یوزرنیم: @{getattr(user, 'username', None) or '—'}"
        )
        await event.reply(text)
