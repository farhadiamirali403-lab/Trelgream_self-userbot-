# Telegram Integration

## Credentials

- `api_id` / `api_hash` از [my.telegram.org](https://my.telegram.org) — در `.env` قرار می‌گیرند (هرگز hardcode).
- `CENTRAL_BOT_TOKEN` از [@BotFather](https://t.me/BotFather).

## Authorization Flow

```
send_code_request(phone)  →  دریافت phone_code_hash + sentCodeType
   ↓
نمایش روش ارسال بر اساس sentCodeType (app/sms/call/email/fragment/other)
   ↓
sign_in(phone, code, phone_code_hash)
   ├─ موفق → session
   └─ SessionPasswordNeededError → sign_in(password=2FA)
```

- **کد هرگز SMS فرض نمی‌شود**؛ UI بر اساس `sentCodeType` داینامیک است.
- state موقت احراز (phone_code_hash + session) **رمزنگاری‌شده** در Redis با TTL نگه‌داری می‌شود.
- `FloodWaitError` به‌صورت `TelegramFloodWaitError` ترجمه و به کاربر اعلام می‌شود.

## Session

- Telethon `StringSession` → رمزنگاری با `SessionCipher` → ذخیره در `telegram_sessions`.
- رمزگشایی فقط در Worker برای ساخت `TelegramClient`.

## Rate limits

- login: 5 درخواست / 5 دقیقه
- code verify: 3 درخواست / 10 دقیقه
