"""Userbot service: creation, lifecycle commands, status."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import SessionCipher
from app.database.models.telegram import TelegramAccount, TelegramSession
from app.database.models.userbots import Userbot
from app.userbots.repository import UserbotRepository
from app.workers.commands import CommandBus


def _now() -> datetime:
    return datetime.now(timezone.utc)


class UserbotService:
    def __init__(
        self,
        session: AsyncSession,
        cipher: SessionCipher,
        command_bus: CommandBus,
    ) -> None:
        self.session = session
        self.cipher = cipher
        self.command_bus = command_bus
        self.repo = UserbotRepository(session)

    async def complete_authorization(
        self,
        user_id: int,
        phone: str,
        session_string: str,
        *,
        device_model: str | None = None,
    ) -> Userbot:
        """Store the authorized (encrypted) session and create the userbot."""
        account = await self._get_or_create_account(user_id, phone)
        account.is_authorized = True
        account.auth_state = "authorized"

        # Encrypt-at-rest; raw session never touches the DB.
        encrypted = self.cipher.encrypt(session_string)
        session_row = TelegramSession(
            telegram_account_id=account.id,
            encrypted_session=encrypted,
            is_active=True,
            device_model=device_model,
        )
        self.session.add(session_row)
        await self.session.flush()

        userbot = await self._get_or_create_userbot(user_id, account.id)
        userbot.status = "AUTHORIZED"
        await self.session.flush()
        return userbot

    async def request_start(self, userbot_id: int, *, actor_id: int, actor_role: str) -> None:
        userbot = await self.repo.get_or_raise(userbot_id)
        if userbot.status == "RUNNING":
            return
        userbot.status = "STARTING"
        await self.session.flush()
        await self.command_bus.send("start", userbot_id, actor_id=actor_id, actor_role=actor_role)

    async def request_stop(self, userbot_id: int, *, actor_id: int, actor_role: str) -> None:
        userbot = await self.repo.get_or_raise(userbot_id)
        userbot.status = "STOPPING"
        await self.session.flush()
        await self.command_bus.send("stop", userbot_id, actor_id=actor_id, actor_role=actor_role)

    async def request_restart(self, userbot_id: int, *, actor_id: int, actor_role: str) -> None:
        userbot = await self.repo.get_or_raise(userbot_id)
        await self.command_bus.send("restart", userbot_id, actor_id=actor_id, actor_role=actor_role)

    async def revoke_sessions(self, userbot_id: int) -> int:
        """Revoke all sessions for a userbot (logout capability)."""
        userbot = await self.repo.get_or_raise(userbot_id)
        stmt = select(TelegramSession).where(
            TelegramSession.telegram_account_id == userbot.telegram_account_id,
            TelegramSession.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        for row in rows:
            row.is_active = False
            row.revoked_at = _now()
        await self.session.flush()
        return len(rows)

    # --- internal helpers ---

    async def _get_or_create_account(self, user_id: int, phone: str) -> TelegramAccount:
        stmt = select(TelegramAccount).where(
            TelegramAccount.user_id == user_id, TelegramAccount.phone == phone
        )
        result = await self.session.execute(stmt)
        account = result.scalar_one_or_none()
        if account is None:
            account = TelegramAccount(user_id=user_id, phone=phone)
            self.session.add(account)
            await self.session.flush()
        return account

    async def _get_or_create_userbot(self, user_id: int, account_id: int) -> Userbot:
        stmt = select(Userbot).where(Userbot.telegram_account_id == account_id)
        result = await self.session.execute(stmt)
        userbot = result.scalar_one_or_none()
        if userbot is None:
            userbot = Userbot(user_id=user_id, telegram_account_id=account_id)
            self.session.add(userbot)
            await self.session.flush()
        return userbot
