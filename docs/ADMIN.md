# Admin / Owner Panel

## دسترسی

- Owner = `OWNER_TELEGRAM_ID` در `.env` (به‌صورت خودکار نقش OWNER دارد).
- ادمین‌های دیگر از جدول `admins` با نقش و permission تعیین می‌شوند.

## دستورات

- `/admin` — پنل ادمین (فقط ادمین‌ها)
- مدیریت پرداخت‌ها (تأیید/رد)، مشاهدهٔ Userbotها، کاربران و آمار.

## Permission Matrix (خلاصه)

| Permission | OWNER | SUPER_ADMIN | ADMIN | MODERATOR | SUPPORT |
|---|---|---|---|---|---|
| users.view | ✅ | ✅ | ✅ | ✅ | ❌ |
| users.edit / suspend | ✅ | ✅ | ✅/❌ | ❌ | ❌ |
| payments.view / approve / reject | ✅ | ✅ | ✅ | ❌ | ❌ |
| subscriptions.view | ✅ | ✅ | ✅ | ❌ | ✅ |
| userbots.view / start / stop / restart | ✅ | ✅ | ✅ | ❌ | ❌ |
| modules.view / manage | ✅ | ✅ | ✅/❌ | ❌ | ❌ |
| logs.view / settings.view / broadcast | ✅ | ✅ | ✅/❌ | ❌ | ❌ |
| admins.manage | ✅ | ✅ | ❌ | ❌ | ❌ |
| support.manage | ✅ | ✅ | ✅ | ✅ | ✅ |

(ماتریس کامل در `app/auth/permissions.py`)

## Privacy

دسترسی به محتوای پیام کاربران نیازمند permission مجزا (`messages.view`) است و
به‌صورت پیش‌فرض فعال نیست.
