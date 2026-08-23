"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routers import admin, auth_web, health, plans
from app.core.exceptions import AppError


def create_app() -> FastAPI:
    app = FastAPI(
        title="Telegram Userbot SaaS",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.include_router(health.router)
    app.include_router(plans.router)
    app.include_router(admin.router)
    app.include_router(auth_web.router)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    return app


app = create_app()
