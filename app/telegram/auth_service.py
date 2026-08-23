"""Telegram authorization state machine (dynamic, 2FA-aware, FloodWait-safe).

The verification code is NEVER assumed to be SMS: the UI is driven by the
``sentCodeType`` returned by Telegram (app / sms / call / flash-call / email /
fragment / other).
"""

from __future__ import annotations

from dataclasses import dataclass

from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError,
    PasswordHashInvalidError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
)
from telethon.tl import types

from app.core.exceptions import (
    TelegramAuthError,
    TelegramFloodWaitError,
    ValidationError,
)
from app.core.redis import AuthStateStore
from app.core.security import SessionCipher
from app.telegram.client_factory import build_user_client

_CODE_TYPE_MESSAGES = {
    "app": "کد تأیید به تلگرام شما ارسال شد (چت تلگرام / Telegram).",
    "sms": "کد تأیید از طریق پیامک (SMS) ارسال شد.",
    "call": "تلگرام با شما تماس خواهد گرفت و کد را اعلام می‌کند.",
    "flash_call": "یک تماس فلش دریافت می‌کنید؛ آخرین ارقام شماره، کد است.",
    "email": "کد تأیید به ایمیل شما ارسال شد.",
    "fragment_sms": "کد تأیید از طریق Fragment SMS ارسال شد.",
    "other": "تلگرام کد تأیید را از روش دیگری ارسال می‌کند؛ آن را وارد کنید.",
}


def describe_sent_code(sent: types.auth.SentCode) -> dict:
    """Map a Telegram SentCode to a stable method name and Persian message."""
    type_ = sent.type
    if isinstance(type_, types.auth.SentCodeTypeApp):
        method = "app"
        length = getattr(type_, "length", None)
    elif isinstance(type_, types.auth.SentCodeTypeSms):
        method = "sms"
        length = getattr(type_, "length", None)
    elif isinstance(type_, types.auth.SentCodeTypeCall):
        method = "call"
        length = getattr(type_, "length", None)
    elif isinstance(type_, types.auth.SentCodeTypeFlashCall):
        method = "flash_call"
        length = None  # code is derived from the phone number
    elif isinstance(type_, types.auth.SentCodeTypeEmailCode):
        method = "email"
        length = getattr(type_, "length", None)
    elif isinstance(type_, types.auth.SentCodeTypeFragmentSms):
        method = "fragment_sms"
        length = getattr(type_, "length", None)
    else:
        method = "other"
        length = None

    return {
        "method": method,
        "message": _CODE_TYPE_MESSAGES[method],
        "code_length": length,
    }


@dataclass
class AuthResult:
    status: str  # "code_sent" | "needs_2fa" | "authorized"
    message: str
    code_method: str | None = None
    code_length: int | None = None
    session_string: str | None = None
    user_phone: str | None = None
    user_id: int | None = None
    first_name: str | None = None


class TelegramAuthService:
    """Orchestrates the multi-step Telegram login using Redis state."""

    def __init__(self, store: AuthStateStore, cipher: SessionCipher, settings) -> None:
        self.store = store
        self.cipher = cipher
        self.settings = settings

    # --- helpers ---

    def _client(self, session_str: str | None) -> TelegramClient:
        return build_user_client(session_str, self.settings)

    @staticmethod
    def _guard_flood(func):
        """Translate Telethon errors into application errors."""

        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except FloodWaitError as exc:
                raise TelegramFloodWaitError(
                    f"محدودیت تلگرام؛ {exc.seconds} ثانیه صبر کنید", code="telegram_flood_wait"
                ) from exc
            except PhoneCodeInvalidError as exc:
                raise ValidationError("کد تأیید نامعتبر است") from exc
            except PhoneCodeExpiredError as exc:
                raise ValidationError("کد تأیید منقضی شده است؛ دوباره درخواست دهید") from exc
            except PasswordHashInvalidError as exc:
                raise ValidationError("رمز 2FA نادرست است") from exc

        return wrapper

    # --- public API ---

    @_guard_flood
    async def send_code(self, phone: str) -> AuthResult:
        client = self._client(None)
        try:
            await client.connect()
            # force_sms=True از مسدود شدن به‌دلیل «اشتراک‌گذاری کد» جلوگیری می‌کند؛
            # کد از طریق پیامک می‌آید و کاربر آن را تایپ می‌کند (نه کپی از چت تلگرام).
            sent = await client.send_code_request(phone, force_sms=True)
            info = describe_sent_code(sent)
            state = {
                "phone": phone,
                "phone_code_hash": sent.phone_code_hash,
                "session": client.session.save(),
            }
            await self.store.save(phone, state)
            return AuthResult(
                status="code_sent",
                message=info["message"],
                code_method=info["method"],
                code_length=info["code_length"],
            )
        finally:
            await client.disconnect()

    @_guard_flood
    async def sign_in_code(self, phone: str, code: str) -> AuthResult:
        state = await self.store.load(phone)
        client = self._client(state["session"])
        try:
            await client.connect()
            try:
                me = await client.sign_in(
                    phone, code, phone_code_hash=state["phone_code_hash"]
                )
            except SessionPasswordNeededError:
                state["session"] = client.session.save()
                state["needs_2fa"] = True
                await self.store.save(phone, state)
                return AuthResult(status="needs_2fa", message="رمز 2FA را وارد کنید")
            return self._authorized(client, phone, me)
        finally:
            await client.disconnect()

    @_guard_flood
    async def sign_in_2fa(self, phone: str, password: str) -> AuthResult:
        state = await self.store.load(phone)
        client = self._client(state["session"])
        try:
            await client.connect()
            me = await client.sign_in(password=password)
            return self._authorized(client, phone, me)
        finally:
            await client.disconnect()

    def _authorized(self, client: TelegramClient, phone: str, me) -> AuthResult:
        session_str = client.session.save()
        return AuthResult(
            status="authorized",
            message="احراز هویت با موفقیت انجام شد",
            session_string=session_str,
            user_phone=phone,
            user_id=getattr(me, "id", None),
            first_name=getattr(me, "first_name", None),
        )
