# Security Model

## Session Security

- نشست تلگرام با **Fernet (AES128-CBC-HMAC)** رمزنگاری و در `telegram_sessions.encrypted_session` ذخیره می‌شود.
- متن خام نشست **هرگز** وارد DB، log، Git، پیام تلگرام یا error message نمی‌شود.
- رمزگشایی فقط در runtime (Worker) انجام می‌شود.
- قابلیت revoke کامل (`UserbotService.revoke_sessions`).

## RBAC

نقش‌ها: `OWNER`, `SUPER_ADMIN`, `ADMIN`, `MODERATOR`, `SUPPORT`.
هر نقش مجموعه‌ای از permissionها دارد (مثلاً `payments.approve`).
OWNER تنها نقش غیرقابل حذف است و همهٔ permissionها را دارد.

## Tenant Isolation

- همهٔ queryها از طریق `BaseRepository.get_for_tenant()` با فیلتر `user_id` انجام می‌شوند.
- دسترسی به منبع tenant دیگر `NotFoundError` برمی‌گرداند (بدون افشای وجود منبع).

## Internal Command Security

دستورات داخلی (start/stop/restart) از طریق Redis ارسال می‌شوند و شامل:
`command_id`, `ts`, `actor`, `target`, `expires_at`, `signature (HMAC)`.
Worker امضا و انقضا را قبل از اجرا بررسی می‌کند (ضد جعل و replay).

## Rate Limiting & FloodWait

- Rate limit روی login، code verify، دستورات ادمین (Redis).
- هندل `FloodWaitError` — بدون retry کور.

## Logging

- لاگ ساختاریافته (JSON) با redaction خودکار برای کلیدهای حساس
  (کد تأیید، رمز 2FA، نشست، api_hash، bot token، encryption key).

## Privacy

ادمین‌ها به‌صورت پیش‌فرض فقط وضعیت/health/technical logs/اشتراک/مصرف را می‌بینند.
دسترسی به محتوای پیام نیازمند permission مجزا (`messages.view`) و پیکربندی صریح است.
