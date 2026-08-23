# Worker Manager

## Responsibilities

- Start / Stop / Restart یوزربات‌ها
- Heartbeat (به `workers` و `userbots.last_heartbeat_at`)
- Health و Load
- Error Recovery

## States

```
STARTING → RUNNING → STOPPING → STOPPED
RUNNING  → ERROR   → RECOVERING → RUNNING
```

## Recovery

```
heartbeat timeout
   ↓
mark unhealthy
   ↓
recovery job
   ↓
restart → reconnect Telegram → restore modules → health check
   ↓
RUNNING
```

Retry با **exponential backoff** (2^n، حداکثر 300 ثانیه).

## Internal commands

دستورات از Redis (`commands:userbots`) خوانده و بعد از تأیید امضا/انقضا اجرا می‌شوند:
`start`, `stop`, `restart`.

## Scheduled tasks

Worker از `tasks:userbots` وظایف ارسال‌شده توسط Scheduler را اجرا می‌کند
(مثلاً `send_message` روی client یوزربات).
