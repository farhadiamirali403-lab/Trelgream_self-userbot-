"""User repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.users import User
from app.database.repository import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self, *, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[User]:
        stmt = select(User)
        if query:
            like = f"%{query}%"
            stmt = stmt.where(
                (User.username.ilike(like))
                | (User.phone.ilike(like))
                | (User.first_name.ilike(like))
            )
        stmt = stmt.order_by(User.id.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
