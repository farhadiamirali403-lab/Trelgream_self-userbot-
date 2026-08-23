# REST API

Swagger/OpenAPI: `http://127.0.0.1:8000/docs`

## Endpoints

| Method | Path | توضیح |
|---|---|---|
| GET | `/health` | وضعیت DB/Redis/Telegram/Workers |
| GET | `/api/plans` | لیست پلن‌های فعال (public) |
| GET | `/api/admin/stats` | آمار کلی (admin) |
| GET | `/api/admin/users` | لیست/جستجوی کاربران (admin) |
| GET | `/api/admin/userbots` | لیست یوزربات‌ها (admin) |
| GET | `/api/admin/payments/pending` | پرداخت‌های در انتظار (admin) |
| POST | `/api/admin/payments/{id}/approve` | تأیید پرداخت (admin) |
| POST | `/api/admin/payments/{id}/reject` | رد پرداخت (admin) |

## Auth

Endpointهای ادمین با هدر `X-Admin-Key` (مقدار `ADMIN_API_KEY` در `.env`) محافظت می‌شوند.
