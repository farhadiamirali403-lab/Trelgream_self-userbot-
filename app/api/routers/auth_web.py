"""Web-based Telegram authorization (avoids Telegram anti-share protection).

The user opens a browser page, enters phone -> code -> 2FA. The code is typed
into a web form (not shared inside a Telegram chat), so Telegram's
"shared login code" protection does not trigger.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.redis import AuthStateStore, get_redis
from app.core.security import CommandSigner, SessionCipher
from app.database.session import async_session_factory
from app.telegram.auth_service import TelegramAuthService
from app.userbots.service import UserbotService
from app.users.service import UserService
from app.workers.commands import CommandBus

router = APIRouter()


@lru_cache
def _services() -> tuple:
    settings = get_settings()
    cipher = SessionCipher(settings.session_encryption_key)
    redis = get_redis()
    store = AuthStateStore(redis, cipher.encrypt, cipher.decrypt)
    auth = TelegramAuthService(store, cipher, settings)
    command_bus = CommandBus(redis, CommandSigner(settings.session_encryption_key or "cmd"))
    return auth, cipher, command_bus


def _page(title: str, body: str) -> HTMLResponse:
    html = f"""<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ font-family: Tahoma, sans-serif; background:#0f172a; color:#e2e8f0;
       display:flex; justify-content:center; align-items:center; min-height:100vh; margin:0; }}
.card {{ background:#1e293b; padding:32px; border-radius:16px; width:360px;
         box-shadow:0 10px 30px rgba(0,0,0,.4); }}
h2 {{ margin-top:0; text-align:center; }}
input {{ width:100%; box-sizing:border-box; padding:12px; margin:8px 0; border-radius:8px;
        border:1px solid #334155; background:#0f172a; color:#e2e8f0; font-size:16px; }}
button {{ width:100%; padding:12px; margin-top:12px; border-radius:8px; border:none;
         background:#2563eb; color:#fff; font-size:16px; cursor:pointer; }}
button:hover {{ background:#1d4ed8; }}
.note {{ font-size:13px; color:#94a3b8; margin:10px 0; line-height:1.6; }}
.ok {{ color:#4ade80; text-align:center; }}
.err {{ color:#f87171; background:#7f1d1d; padding:10px; border-radius:8px; margin:10px 0; }}
a {{ color:#60a5fa; }}
</style>
</head>
<body><div class="card">{body}</div></body>
</html>"""
    return HTMLResponse(html)


async def _complete_auth(tg_id: int, phone: str, session_string: str) -> None:
    auth, cipher, command_bus = _services()
    async with async_session_factory() as session:
        user = await UserService(session).get_or_create(tg_id)
        user.phone = phone
        service = UserbotService(session, cipher, command_bus)
        userbot = await service.complete_authorization(user.id, phone, session_string)
        await service.request_start(userbot.id, actor_id=user.id, actor_role="USER")
        await session.commit()


@router.get("/auth", response_class=HTMLResponse)
async def auth_page(tg: int | None = None):
    body = f"""
<h2>🔗 اتصال حساب تلگرام</h2>
<form method="post" action="/auth/send-code">
  <input type="hidden" name="tg" value="{tg or 0}">
  <div class="note">شماره حساب تلگرام خود را وارد کنید (کد از طریق پیامک یا تلگرام ارسال می‌شود و باید همین‌جا تایپ شود).</div>
  <input type="tel" name="phone" placeholder="+989xxxxxxxxx" required autofocus>
  <button type="submit">ارسال کد</button>
</form>
"""
    return _page("اتصال حساب تلگرام", body)


@router.post("/auth/send-code", response_class=HTMLResponse)
async def send_code(tg: int = Form(0), phone: str = Form(...)):
    auth, _, _ = _services()
    try:
        result = await auth.send_code(phone.strip())
    except AppError as exc:
        return _page("خطا", f'<div class="err">{exc.message}</div><a href="/auth?tg={tg}">بازگشت</a>')
    body = f"""
<h2>📲 کد تأیید</h2>
<div class="note">{result.message}</div>
<form method="post" action="/auth/verify-code">
  <input type="hidden" name="tg" value="{tg}">
  <input type="hidden" name="phone" value="{phone.strip()}">
  <input type="text" name="code" placeholder="کد تأیید" required autofocus inputmode="numeric">
  <button type="submit">تأیید</button>
</form>
"""
    return _page("کد تأیید", body)


@router.post("/auth/verify-code", response_class=HTMLResponse)
async def verify_code(tg: int = Form(0), phone: str = Form(...), code: str = Form(...)):
    auth, _, _ = _services()
    try:
        result = await auth.sign_in_code(phone.strip(), code.strip())
    except AppError as exc:
        return _page("خطا", f'<div class="err">{exc.message}</div>')
    if result.status == "needs_2fa":
        body = f"""
<h2>🔐 رمز دومرحله‌ای</h2>
<div class="note">{result.message}</div>
<form method="post" action="/auth/verify-2fa">
  <input type="hidden" name="tg" value="{tg}">
  <input type="hidden" name="phone" value="{phone.strip()}">
  <input type="password" name="password" placeholder="رمز 2FA" required autofocus>
  <button type="submit">ورود</button>
</form>
"""
        return _page("رمز 2FA", body)
    await _complete_auth(tg, phone.strip(), result.session_string)
    return _page("موفق", '<div class="ok">✅ احراز هویت با موفقیت انجام شد!<br><br>Userbot شما در حال اجراست.</div>')


@router.post("/auth/verify-2fa", response_class=HTMLResponse)
async def verify_2fa(tg: int = Form(0), phone: str = Form(...), password: str = Form(...)):
    auth, _, _ = _services()
    try:
        result = await auth.sign_in_2fa(phone.strip(), password)
    except AppError as exc:
        return _page("خطا", f'<div class="err">{exc.message}</div>')
    await _complete_auth(tg, phone.strip(), result.session_string)
    return _page("موفق", '<div class="ok">✅ احراز هویت با موفقیت انجام شد!<br><br>Userbot شما در حال اجراست.</div>')
