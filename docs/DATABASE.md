# Database

PostgreSQL 16 به‌عنوان منبع حقیقت دائمی. همهٔ تغییرات از طریق **Alembic** انجام می‌شود.

## Tables (30)

| گروه | جداول |
|---|---|
| Identity | `users` |
| RBAC | `admins`, `roles`, `permissions`, `role_permissions`, `admin_roles` |
| Telegram | `telegram_accounts`, `telegram_sessions` |
| Userbot | `userbots`, `workers`, `worker_heartbeats` |
| Billing | `plans`, `subscriptions`, `payments`, `payment_receipts` |
| Modules | `modules`, `user_modules`, `module_settings` |
| Automation | `automation_rules`, `automation_conditions`, `automation_actions` |
| Scheduler | `scheduled_tasks` |
| Support | `notifications`, `support_tickets` |
| Logs | `audit_logs`, `system_logs`, `error_logs` |
| Settings | `settings`, `payment_settings` |
| Analytics | `usage_metrics` |

## Key relationships

- `users` ریشهٔ tenant است؛ همهٔ موجودیت‌های کاربر به `user_id` متصل‌اند.
- `telegram_accounts` (شماره) → `telegram_sessions` (نشست رمزنگاری‌شده).
- `userbots` نمونهٔ اجرایی است که روی یک `workers` اجرا می‌شود.
- `payments` → `subscriptions` → `plans` زنجیرهٔ مالی.

## Migrations

```powershell
alembic revision --autogenerate -m "..."   # ساخت migration
alembic upgrade head                        # اعمال
```

## Type notes

- PK: `BIGINT` روی PostgreSQL، `INTEGER` روی SQLite (برای تست).
- JSON: `JSONB` روی PostgreSQL، `JSON` روی SQLite.
