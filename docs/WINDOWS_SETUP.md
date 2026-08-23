# Windows Setup

## 1. پیش‌نیاز

- Python 3.12/3.13 از [python.org](https://python.org) (Add to PATH).
- `api_id` / `api_hash` از my.telegram.org + توکن ربات از BotFather.

## 2. نصب

```powershell
cd C:\telegram-saas
.\scripts\setup.ps1
```

این اسکریپت: venv می‌سازد، وابستگی‌ها را نصب می‌کند،
PostgreSQL و Redis قابل‌حمل را دانلود و راه‌اندازی می‌کند،
`.env` می‌سازد و دیتابیس/migration/seed را اجرا می‌کند.

## 3. پیکربندی `.env`

```env
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
CENTRAL_BOT_TOKEN=...
OWNER_TELEGRAM_ID=...
```

## 4. اجرا

```powershell
.\scripts\start.ps1
.\scripts\status.ps1
.\scripts\stop.ps1
.\scripts\restart.ps1
```

یا اجرای جداگانهٔ هر فرایند:

```powershell
python -m app.api
python -m app.bot
python -m app.workers
python -m app.scheduler
```

## نکات

- PostgreSQL و Redis در `.runtime/` نصب می‌شوند (بدون نیاز به admin).
- Redis ویندوزی نسخه 5.0 است؛ بنابراین کلاینت با `protocol=2` کار می‌کند.
