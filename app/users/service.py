"""User service: find-or-create platform users."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.users import User
from app.users.repository import UserRepository


def _now() -> datetime:
    return datetime.now(timezone.utc)


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = UserRepository(session)

    async def get_or_create(
        self,
        telegram_id: int,
        *,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        user = await self.repo.get_by_telegram_id(telegram_id)
        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                last_active_at=_now(),
            )
            user = await self.repo.add(user)
        else:
            user.username = username or user.username
            user.first_name = first_name or user.first_name
            user.last_name = last_name or user.last_name
            user.last_active_at = _now()
        return user

    async def touch(self, user: User) -> None:
        user.last_active_at = _now()
        await self.repo.session.flush()

    async def get(self, user_id: int) -> User:
        return await self.repo.get_or_raise(user_id)
