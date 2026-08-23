"""Userbot repository + encrypted-session loading."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import SessionError
from app.core.security import SessionCipher
from app.database.models.telegram import TelegramSession
from app.database.models.userbots import Userbot
from app.database.repository import BaseRepository


class UserbotRepository(BaseRepository[Userbot]):
    model = Userbot

    async def list_runnable(self, *, limit: int = 1000) -> list[Userbot]:
        """Userbots that should be online (not STOPPED/SUSPENDED/ERROR)."""
        stmt = (
            select(Userbot)
            .where(Userbot.status.in_(["STARTING", "RUNNING", "RECOVERING", "AUTHORIZED"]))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, *, limit: int = 1000) -> list[Userbot]:
        stmt = select(Userbot).order_by(Userbot.id.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_session(self, telegram_account_id: int, cipher: SessionCipher) -> str:
        """Decrypt the active session string for an account."""
        stmt = (
            select(TelegramSession)
            .where(
                TelegramSession.telegram_account_id == telegram_account_id,
                TelegramSession.is_active.is_(True),
                TelegramSession.revoked_at.is_(None),
            )
            .order_by(TelegramSession.id.desc())
        )
        result = await self.session.execute(stmt)
        session_row = result.scalars().first()
        if session_row is None:
            raise SessionError("نشست فعال یافت نشد")
        return cipher.decrypt(session_row.encrypted_session)
