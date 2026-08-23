# Deployment (Linux VPS)

## مسیر انتقال

```
Windows (local dev)
   ↓
Docker Compose
   ↓
Linux VPS
```

Business logic هیچ وابستگی به pathهای ویندوزی ندارد؛ فقط زیرساخت و process management
عوض می‌شود.

## Docker Compose (توصیه)

فقط زیرساخت را کانتینری کنید؛ خود اپلیکیشن می‌تواند native اجرا شود:

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: telegram_saas
  redis:
    image: redis:7
```

## Production checklist

- `APP_ENV=production`, `DEBUG=false`
- `DATABASE_URL`, `REDIS_URL` → سرویس‌های production
- `SESSION_ENCRYPTION_KEY` → مقدار قوی و پایدار
- `ADMIN_API_KEY` → مقدار قوی
- Storage → S3-compatible (`S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_REGION`)
- Nginx reverse proxy + HTTPS (فقط production)
- PostgreSQL/Redis از سرویس‌های مدیریت‌شده یا Docker
- چند Worker Manager برای scale
