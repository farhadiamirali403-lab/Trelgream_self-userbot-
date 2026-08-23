# Telegram Userbot SaaS Platform

پلتفرم چندکاربره، امن و ماژولار برای اجرای **ربات‌های شخصی تلگرام (Userbot)** به‌صورت SaaS.

- **Windows-first** — بدون نیاز به Cloudflare یا Docker
- **Local-first** — همهٔ اجزا روی یک سیستم اجرا می‌شوند
- **Multi-Tenant** — ایزوله‌سازی کامل بین کاربران
- **Modular** — قابلیت‌ها به‌صورت Module/Plugin توسعه داده می‌شوند
- **Secure** — رمزنگاری نشست‌ها، RBAC، Audit Log، دستورات امضاشده

---

## ✨ قابلیت‌های اصلی

| بخش | توضیح |
|---|---|
| Central Bot | ورود، پنل فارسی RTL، مدیریت از داخل تلگرام |
| احراز هویت تلگرام | پشتیبانی از SMS / Telegram / Email / Call و **2FA** (داینامیک) |
| امنیت نشست | رمزنگاری `Fernet` (encrypted-at-rest)، قابلیت revoke |
| اشتراک | پلن‌های Basic / Pro / Premium / Business با محدودیت قابل تنظیم |
| پرداخت کارت به کارت | نمایش شماره کارت، آپلود رسید، تأیید/رد توسط ادمین |
| Userbot Engine | Worker Manager، heartbeat، recovery با exponential backoff |
| Module System | ثبت، فعال/غیرفعال‌سازی، تنظیمات، permission و محدودیت پلن |
| Automation Engine | Trigger → Conditions (AND/OR) → Actions |
| Scheduler | وظایف یک‌بار / روزانه / هفتگی / ماهانه / بازه‌ای |
| پنل Owner/Admin | کاربران، پرداخت‌ها، اشتراک‌ها، Userbotها، آمار (RBAC) |
| REST API | FastAPI + Swagger/OpenAPI |
| Monitoring | `/health`، لاگ ساختاریافته، متریک‌های Worker |

---

## 🧰 Stack

- **Python 3.12/3.13** — FastAPI، Pydantic v2، SQLAlchemy 2 (async)، Alembic
- **Telethon 1.44** — MTProto برای Central Bot و Userbotها
- **PostgreSQL 16** — منبع حقیقت دائمی (portable روی Windows)
- **Redis** — queue / cache / lock / rate limit / state (portable روی Windows)
- **psycopg3** — درایور async سازگار با Windows

---

## 🚀 راه‌اندازی سریع (Windows)

### پیش‌نیاز

1. نصب **Python 3.12 یا 3.13** از [python.org](https://python.org) (گزینه Add to PATH را بزنید).
2. دریافت `api_id` و `api_hash` از [my.telegram.org](https://my.telegram.org).
3. ساخت Central Bot و دریافت توکن از [@BotFather](https://t.me/BotFather).

PostgreSQL و Redis **به‌صورت خودکار و portable** دانلود و راه‌اندازی می‌شوند (بدون نیاز به admin).

### نصب و اجرا

```powershell
cd C:\telegram-saas
.\scripts\setup.ps1        # نصب وابستگی‌ها + زیرساخت + دیتابیس
```

سپس فایل `.env` را باز کرده و این مقادیر را وارد کنید:

```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=xxxxxxxxxxxxxxxx
CENTRAL_BOT_TOKEN=123456:ABC...
OWNER_TELEGRAM_ID=987654321
```

و در نهایت:

```powershell
.\scripts\start.ps1        # اجرای همهٔ فرایندها
.\scripts\status.ps1       # وضعیت + health check
.\scripts\stop.ps1         # توقف
```

بعد از اجرا:

- **Backend API + Swagger:** http://127.0.0.1:8000/docs
- **Health:** http://127.0.0.1:8000/health
- **Central Bot:** در تلگرام به ربات خود `/start` بدهید.

---

## 📁 ساختار پروژه

```
telegram-saas/
├── app/
│   ├── api/          # FastAPI + routers + Swagger
│   ├── bot/          # Central Bot (Persian UI) + Admin panel
│   ├── core/         # config, logging, exceptions, security, redis, eventloop
│   ├── auth/         # RBAC (permissions, roles)
│   ├── users/        # کاربران (tenant root)
│   ├── billing/      # پلن، اشتراک، پرداخت، رسید
│   ├── telegram/     # Telethon client + auth state machine
│   ├── userbots/     # userbot domain + runtime
│   ├── workers/      # worker manager + commands + recovery
│   ├── modules/      # module registry + builtin modules
│   ├── automation/   # rule engine (trigger/condition/action)
│   ├── scheduler/    # scheduler + scheduled tasks
│   ├── security/     # audit logging
│   ├── storage/      # local + S3-compatible storage
│   └── database/     # base, session, models, repositories, seed
├── migrations/       # Alembic
├── tests/            # pytest (29 test)
├── scripts/          # setup/start/stop/status/restart (PowerShell)
├── docs/             # مستندات
├── .env.example
├── pyproject.toml
└── run.ps1           # launcher
```

---

## 🧪 تست

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

شامل تست‌های: امنیت (رمزنگاری/هش/امضا)، موتور conditions، scheduler، billing/اشتراک/پرداخت، ایزوله‌سازی tenant و RBAC.

---

## 🔐 امنیت

- نشست‌ها با **Fernet** رمزنگاری می‌شوند؛ متن خام هرگز در DB/log/Git نمی‌رود.
- RBAC با نقش‌های OWNER / SUPER_ADMIN / ADMIN / MODERATOR / SUPPORT.
- همهٔ queryها **tenant-aware** هستند.
- دستورات داخلی **امضاشده (HMAC)** با expiration و replay protection.
- Rate limiting روی login/code/ادمین و هندل `FloodWait`.
- Audit log برای تمام عملیات حساس.

مستندات کامل در [`docs/SECURITY.md`](docs/SECURITY.md) و [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## 📚 مستندات بیشتر

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — معماری و فرایندها
- [SECURITY.md](docs/SECURITY.md) — مدل امنیتی
- [DATABASE.md](docs/DATABASE.md) — اسکیما و ERD
- [TELEGRAM.md](docs/TELEGRAM.md) — احراز هویت و Telethon
- [WORKERS.md](docs/WORKERS.md) — Worker Manager و recovery
- [MODULES.md](docs/MODULES.md) — سیستم ماژول
- [API.md](docs/API.md) — REST API
- [ADMIN.md](docs/ADMIN.md) — پنل ادمین و permission matrix
- [USER_GUIDE.md](docs/USER_GUIDE.md) — راهنمای کاربر
- [WINDOWS_SETUP.md](docs/WINDOWS_SETUP.md) — راه‌اندازی Windows
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — رفع اشکال
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) — انتقال به Linux VPS
