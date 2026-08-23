"""Generic async repository with mandatory tenant isolation.

Handlers must never access the database directly. Flow is:

    Handler -> Service -> Repository -> Database

Every user-scoped read/write MUST pass ``tenant_id`` (the owning user id).
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, TenantViolationError
from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """CRUD repository base with tenant-scoped helpers."""

    model: type[ModelT]
    tenant_column: str = "user_id"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- generic CRUD ---

    async def get(self, id_: int) -> ModelT | None:
        return await self.session.get(self.model, id_)

    async def get_or_raise(self, id_: int) -> ModelT:
        obj = await self.get(id_)
        if obj is None:
            raise NotFoundError(f"{self.model.__name__} #{id_} یافت نشد")
        return obj

    async def get_for_tenant(self, id_: int, tenant_id: int) -> ModelT:
        """Fetch a row and enforce tenant ownership (raises NotFound on mismatch)."""
        obj = await self.get(id_)
        if obj is None:
            raise NotFoundError(f"{self.model.__name__} #{id_} یافت نشد")
        if not self._is_owned(obj, tenant_id):
            # Do not leak existence of another tenant's resource.
            raise NotFoundError(f"{self.model.__name__} #{id_} یافت نشد")
        return obj

    async def list_for_tenant(
        self, tenant_id: int, *, limit: int = 50, offset: int = 0, **filters: Any
    ) -> list[ModelT]:
        stmt = select(self.model).where(getattr(self.model, self.tenant_column) == tenant_id)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        stmt = stmt.order_by(self.model.id.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete(self, obj: ModelT) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    # --- tenant helpers ---

    def _is_owned(self, obj: ModelT, tenant_id: int) -> bool:
        owner = getattr(obj, self.tenant_column, None)
        if owner is None:
            raise TenantViolationError(f"{self.model.__name__} مالکیت tenant ندارد")
        return owner == tenant_id

    async def assert_tenant(self, id_: int, tenant_id: int) -> ModelT:
        return await self.get_for_tenant(id_, tenant_id)
