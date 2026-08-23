# Troubleshooting

## `Psycopg cannot use the 'ProactorEventLoop'`

روی Windows باید SelectorEventLoop استفاده شود. همهٔ entry pointها
`configure_event_loop()` را صدا می‌زنند. اگر با uvicorn اجرا می‌کنید، `loop="none"` را بگذارید.

## `unknown command HELLO` (Redis)

Redis ویندوزی (نسخه 5) از RESP3 پشتیبانی نمی‌کند. کلاینت با `protocol=2` ساخته می‌شود
(`app/core/redis.py`). اگر redis-py را ارتقا دادید مطمئن شوید `protocol=2` باقی بماند.

## PostgreSQL دانلود نمی‌شود (403)

EDB از برخی IPها مسدود است؛ پروژه از Maven Central
(`io.zonky.test.postgres:embedded-postgres-binaries-windows-amd64`) استفاده می‌کند.

## `python -m app.X` → `ModuleNotFoundError: app`

از ریشهٔ پروژه (`C:\telegram-saas`) اجرا کنید. اسکریپت‌های `scripts/` مسیر را خودکار اضافه می‌کنند.

## Userbot متصل نمی‌شود

- مطمئن شوید `api_id`/`api_hash` صحیح است.
- نشست ممکن است منقضی شده باشد → «🔄 اتصال مجدد».
- `FloodWait` → صبر کنید و retry نکنید.

## لاگ‌ها

```powershell
Get-Content .runtime\logs\backend.err.log -Tail 50
Get-Content .runtime\logs\worker_manager.err.log -Tail 50
```
