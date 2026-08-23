# Module System

هر قابلیت یکی از حالت‌های `CORE` / `MODULE` / `PLUGIN` را دارد.

## ساختار ماژول

```python
class AutoReplyModule(BaseModule):
    metadata = ModuleMetadata(
        key="auto_reply",
        name="پاسخ خودکار",
        category="message",
        permission="module.auto_reply.use",
        default_enabled=False,
    )

    @handler("new_message")
    async def on_message(self, event):
        ...
```

- `ModuleRegistry` ماژول‌ها را کشف و نگه‌داری می‌کند.
- `ModuleManager` فعال/غیرفعال‌سازی و تنظیمات را با **محدودیت پلن** مدیریت می‌کند.
- هر ماژول permission دارد (مثلاً `module.auto_reply.use`).
- Core فقط discovery / lifecycle / permissions / enable-disable / configuration / dependencies را انجام می‌دهد.

## ماژول‌های داخلی (نمونه)

`auto_reply`, `keyword_reply`, `welcome`, `anti_link` — برای افزودن ماژول جدید کافی است
یک کلاس از `BaseModule` بنویسید و در `app/modules/builtin/__init__.py` ثبت کنید.

## Event types

`new_message`, `edited_message`, `deleted_message` (نگاشت به Telethon events).
