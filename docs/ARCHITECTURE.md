# Architecture

## Overview

معماری چند-فرایندی با هستهٔ کوچک و module/plugin محور:

```
Windows PC
├── FastAPI Backend      (REST + Swagger)
├── Central Telegram Bot (ورود / پنل / پرداخت)
├── Worker Manager       (supervisor یوزربات‌ها)
├── Scheduler            (انقضای اشتراک + وظایف)
├── PostgreSQL           (منبع حقیقت دائمی)
├── Redis                (queue / cache / lock / rate limit / state)
└── Local File Storage   (رسیدها)
```

## Processes

| Process | Entry | مسئولیت |
|---|---|---|
| `backend` | `python -m app.api` | REST API + `/health` + Swagger |
| `central_bot` | `python -m app.bot` | تعامل کاربران + پنل ادمین |
| `worker_manager` | `python -m app.workers` | اجرا/توقف/بازیابی یوزربات‌ها |
| `scheduler` | `python -m app.scheduler` | انقضا، وظایف زمان‌بندی‌شده |

ارتباط بین فرایندها فقط از طریق **Redis** (دستورات امضاشده) و **PostgreSQL** (state دائمی) انجام می‌شود.

## Layers

```
Handler (Telethon / FastAPI)
   ↓
Service (business logic)
   ↓
Repository (tenant-aware data access)
   ↓
Database
```

## Worker Architecture

```
Worker Manager (supervisor)
├── heartbeat / health / recovery / scheduling
├── command queue consumer (signed commands)
└── Userbot runtimes (asyncio tasks)
    ├── Telethon client + modules + automation
    └── ...
```

States: `STARTING → RUNNING → STOPPING → STOPPED` و مسیر خطا `RUNNING → ERROR → RECOVERING → RUNNING`.

## Event Loop (Windows)

روی Windows از `SelectorEventLoop` استفاده می‌شود (psycopg3 async با Proactor سازگار نیست).
تابع `app.core.eventloop.configure_event_loop()` در ابتدای هر entry point فراخوانی می‌شود.

## Scale path

MVP یک Worker Manager با یوزربات‌ها به‌صورت task اجرا می‌کند. معماری برای
multi-worker (چند Worker Manager) و انتقال به Linux/Docker آماده است.
