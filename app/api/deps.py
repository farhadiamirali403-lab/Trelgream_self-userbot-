"""API dependencies: DB session and admin authorization."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.session import get_session

SessionDep = Depends(get_session)


async def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    """Protect admin endpoints with a static API key (X-Admin-Key header)."""
    settings = get_settings()
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="ADMIN_API_KEY تنظیم نشده است")
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="دسترسی غیرمجاز")
