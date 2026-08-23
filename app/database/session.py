"""Async engine and session management."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


def create_engine(url: str | None = None) -> AsyncEngine:
    """Create an async engine. URL defaults to settings.database_url."""
    settings = get_settings()
    target = url or settings.database_url
    return create_async_engine(
        target,
        echo=settings.debug,
        pool_pre_ping=True,
        future=True,
    )


# Module-level engine/session factory (no connection is opened at import time).
engine: AsyncEngine = create_engine()
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a scoped async session."""
    async with async_session_factory() as session:
        yield session
