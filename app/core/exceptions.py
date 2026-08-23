"""Structured application exception hierarchy."""

from __future__ import annotations


class AppError(Exception):
    """Base class for all application errors."""

    code: str = "app_error"
    status_code: int = 400
    message: str = "خطای برنامه"

    def __init__(self, message: str | None = None, *, code: str | None = None) -> None:
        self.message = message or self.message
        if code:
            self.code = code
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message}


class NotFoundError(AppError):
    code = "not_found"
    status_code = 404
    message = "یافت نشد"


class PermissionDeniedError(AppError):
    code = "permission_denied"
    status_code = 403
    message = "دسترسی مجاز نیست"


class AuthenticationError(AppError):
    code = "authentication_error"
    status_code = 401
    message = "احراز هویت ناموفق"


class TenantViolationError(PermissionDeniedError):
    code = "tenant_violation"
    message = "دسترسی به این منبع مجاز نیست"


class ValidationError(AppError):
    code = "validation_error"
    status_code = 422
    message = "داده نامعتبر است"


class RateLimitError(AppError):
    code = "rate_limited"
    status_code = 429
    message = "درخواست بیش از حد؛ کمی بعد تلاش کنید"


class ConflictError(AppError):
    code = "conflict"
    status_code = 409
    message = "تداخل در وضعیت فعلی"


class ServiceUnavailableError(AppError):
    code = "service_unavailable"
    status_code = 503
    message = "سرویس در دسترس نیست"


class NotConfiguredError(AppError):
    code = "not_configured"
    status_code = 500
    message = "پیکربندی کامل نیست"


class ModuleNotImplementedError(AppError):
    """Raised by modules whose feature is declared but not yet built."""

    code = "not_implemented"
    status_code = 501
    message = "این قابلیت هنوز پیاده‌سازی نشده است (NOT IMPLEMENTED)"


class TelegramAuthError(AppError):
    code = "telegram_auth_error"
    message = "خطا در احراز هویت تلگرام"


class TelegramFloodWaitError(AppError):
    code = "telegram_flood_wait"
    status_code = 429
    message = "محدودیت تلگرام؛ لطفاً صبر کنید"


class SessionError(AppError):
    code = "session_error"
    message = "خطا در نشست"
