"""Feature catalog: 129 declared features (implemented + declared-not-implemented).

Each entry maps to the master-prompt section 31. Implemented modules are real
classes in this package; the rest are declared here with ``not_implemented=True``
so they appear in the panel and are gated by the plugin system.
"""

from __future__ import annotations

CATALOG: list[dict] = [
    # ---- message ----
    {"key": "regex_reply", "name": "پاسخ با الگو", "category": "message", "description": "پاسخ بر اساس الگوی Regex"},
    {"key": "message_filter", "name": "فیلتر پیام", "category": "message", "description": "فیلتر پیام‌های ورودی"},
    {"key": "message_search", "name": "جستجوی پیام", "category": "message", "description": "جستجوی پیام در چت‌ها"},
    {"key": "message_stats", "name": "آمار پیام", "category": "message", "description": "آمار پیام‌ها"},
    {"key": "scheduled_messages", "name": "پیام زمان‌بندی", "category": "message", "description": "ارسال پیام زمان‌بندی‌شده"},
    # ---- groups ----
    {"key": "admin_manager", "name": "مدیریت ادمین", "category": "groups", "description": "مدیریت ادمین‌های گروه"},
    {"key": "group_stats", "name": "آمار گروه", "category": "groups", "description": "آمار اعضا و فعالیت گروه"},
    # ---- channels ----
    {"key": "channel_auto_delete", "name": "حذف خودکار کانال", "category": "channels", "description": "حذف خودکار پست‌ها"},
    {"key": "post_stats", "name": "آمار پست", "category": "channels", "description": "آمار بازدید پست‌ها"},
    {"key": "media_publishing", "name": "انتشار رسانه", "category": "channels", "description": "انتشار خودکار رسانه"},
    {"key": "caption_manager", "name": "مدیریت کپشن", "category": "channels", "description": "مدیریت کپشن پست‌ها"},
    {"key": "hashtag_manager", "name": "مدیریت هشتگ", "category": "channels", "description": "مدیریت هشتگ‌ها"},
    {"key": "channel_monitor", "name": "مانیتور کانال", "category": "channels", "description": "پایش کانال‌ها"},
    {"key": "cross_posting", "name": "پست‌گذاری متقاطع", "category": "channels", "description": "انتشار هم‌زمان در چند کانال"},
    # ---- automation ----
    {"key": "trigger_engine", "name": "موتور تریگر", "category": "automation", "description": "موتور تریگر رویدادها"},
    {"key": "rule_engine", "name": "موتور قانون", "category": "automation", "description": "موتور قوانین"},
    {"key": "event_action", "name": "رویداد و عمل", "category": "automation", "description": "نگاشت رویداد به عمل"},
    {"key": "scheduler_core", "name": "زمان‌بند", "category": "automation", "description": "زمان‌بندی وظایف"},
    {"key": "recurring_tasks", "name": "وظایف تکراری", "category": "automation", "description": "وظایف تکراری"},
    {"key": "conditions", "name": "شرط‌ها", "category": "automation", "description": "شرط‌های قانون"},
    {"key": "workflows", "name": "گردش‌کار", "category": "automation", "description": "گردش‌کارهای چندمرحله‌ای"},
    {"key": "forward_rules", "name": "قوانین فوروارد", "category": "automation", "description": "قوانین فوروارد خودکار"},
    {"key": "reply_rules", "name": "قوانین پاسخ", "category": "automation", "description": "قوانین پاسخ خودکار"},
    {"key": "user_rules", "name": "قوانین کاربر", "category": "automation", "description": "قوانین بر اساس کاربر"},
    {"key": "chat_rules", "name": "قوانین چت", "category": "automation", "description": "قوانین بر اساس چت"},
    {"key": "time_rules", "name": "قوانین زمان", "category": "automation", "description": "قوانین بر اساس زمان"},
    {"key": "regex_rules", "name": "قوانین Regex", "category": "automation", "description": "قوانین مبتنی بر الگو"},
    {"key": "webhook_trigger", "name": "تریگر وب‌هوک", "category": "automation", "description": "فعال‌سازی با وب‌هوک"},
    {"key": "api_trigger", "name": "تریگر API", "category": "automation", "description": "فعال‌سازی با API"},
    # ---- media ----
    {"key": "uploader", "name": "آپلودر", "category": "media", "description": "آپلود فایل"},
    {"key": "image_tools", "name": "ابزار تصویر", "category": "media", "description": "ابزارهای پردازش تصویر"},
    {"key": "video_tools", "name": "ابزار ویدیو", "category": "media", "description": "ابزارهای پردازش ویدیو"},
    {"key": "audio_tools", "name": "ابزار صدا", "category": "media", "description": "ابزارهای پردازش صدا"},
    {"key": "voice_tools", "name": "ابزار ویس", "category": "media", "description": "ابزارهای پردازش ویس"},
    {"key": "thumbnail", "name": "تصویر بندانگشتی", "category": "media", "description": "ساخت تصویر بندانگشتی"},
    {"key": "converter", "name": "تبدیل‌گر", "category": "media", "description": "تبدیل فرمت رسانه"},
    # ---- search ----
    {"key": "message_search2", "name": "جستجوی پیام", "category": "search", "description": "جستجوی پیشرفته پیام"},
    {"key": "chat_search", "name": "جستجوی چت", "category": "search", "description": "جستجوی چت‌ها"},
    {"key": "history_search", "name": "جستجوی تاریخچه", "category": "search", "description": "جستجو در تاریخچه"},
    {"key": "statistics", "name": "آمار", "category": "search", "description": "آمار و گزارش‌ها"},
    # ---- plugins ----
    {"key": "plugin_manager", "name": "مدیر پلاگین", "category": "plugins", "description": "مدیریت پلاگین‌ها"},
    {"key": "plugin_toggle", "name": "فعال/غیرفعال پلاگین", "category": "plugins", "description": "فعال‌سازی پلاگین"},
    {"key": "plugin_config", "name": "پیکربندی پلاگین", "category": "plugins", "description": "تنظیمات پلاگین"},
    {"key": "plugin_reload", "name": "بارگذاری مجدد", "category": "plugins", "description": "بارگذاری مجدد پلاگین"},
    {"key": "plugin_deps", "name": "وابستگی‌ها", "category": "plugins", "description": "مدیریت وابستگی پلاگین"},
    {"key": "plugin_permissions", "name": "مجوزها", "category": "plugins", "description": "مجوزهای پلاگین"},
    {"key": "plugin_versioning", "name": "نسخه‌بندی", "category": "plugins", "description": "نسخه‌بندی پلاگین"},
    {"key": "plugin_logs", "name": "لاگ پلاگین", "category": "plugins", "description": "گزارش پلاگین‌ها"},
    {"key": "plugin_marketplace", "name": "بازارچه پلاگین", "category": "plugins", "description": "بازارچه پلاگین"},
    {"key": "custom_plugins", "name": "پلاگین سفارشی", "category": "plugins", "description": "پلاگین‌های سفارشی"},
    # ---- system ----
    {"key": "sys_start", "name": "شروع", "category": "system", "description": "شروع سلف"},
    {"key": "sys_stop", "name": "توقف", "category": "system", "description": "توقف سلف"},
    {"key": "sys_restart", "name": "ری‌استارت", "category": "system", "description": "ری‌استارت سلف"},
    {"key": "config_reload", "name": "بارگذاری کانفیگ", "category": "system", "description": "بارگذاری مجدد تنظیمات"},
    {"key": "backup", "name": "پشتیبان‌گیری", "category": "system", "description": "پشتیبان‌گیری از داده‌ها"},
    {"key": "restore", "name": "بازیابی", "category": "system", "description": "بازیابی از پشتیبان"},
    {"key": "system_logs", "name": "لاگ سیستم", "category": "system", "description": "لاگ‌های سیستم"},
    {"key": "error_logs", "name": "لاگ خطا", "category": "system", "description": "لاگ‌های خطا"},
    {"key": "resource_monitor", "name": "مانیتور منابع", "category": "system", "description": "پایش منابع سیستم"},
    # ---- analytics ----
    {"key": "message_analytics", "name": "تحلیل پیام", "category": "analytics", "description": "تحلیل پیام‌ها"},
    {"key": "user_analytics", "name": "تحلیل کاربر", "category": "analytics", "description": "تحلیل کاربران"},
    {"key": "chat_analytics", "name": "تحلیل چت", "category": "analytics", "description": "تحلیل چت‌ها"},
    {"key": "activity", "name": "فعالیت", "category": "analytics", "description": "پایش فعالیت"},
    {"key": "command_stats", "name": "آمار دستورات", "category": "analytics", "description": "آمار دستورات"},
    {"key": "module_stats", "name": "آمار ماژول", "category": "analytics", "description": "آمار ماژول‌ها"},
    {"key": "worker_stats", "name": "آمار ورکر", "category": "analytics", "description": "آمار ورکرها"},
    # ---- security ----
    {"key": "roles", "name": "نقش‌ها", "category": "security", "description": "مدیریت نقش‌ها"},
    {"key": "permissions", "name": "مجوزها", "category": "security", "description": "مدیریت مجوزها"},
    {"key": "session_manager", "name": "مدیر نشست", "category": "security", "description": "مدیریت نشست‌ها"},
    {"key": "session_revocation", "name": "ابطال نشست", "category": "security", "description": "ابطال نشست‌ها"},
    {"key": "device_monitoring", "name": "مانیتور دستگاه", "category": "security", "description": "پایش دستگاه‌ها"},
    {"key": "security_logs", "name": "لاگ امنیتی", "category": "security", "description": "لاگ‌های امنیتی"},
    {"key": "rate_limiting", "name": "محدودیت نرخ", "category": "security", "description": "محدودیت نرخ درخواست"},
    {"key": "suspicious_activity", "name": "فعالیت مشکوک", "category": "security", "description": "تشخیص فعالیت مشکوک"},
    # ---- integrations ----
    {"key": "rest_api", "name": "REST API", "category": "integrations", "description": "دسترسی REST API"},
    {"key": "webhooks", "name": "وب‌هوک‌ها", "category": "integrations", "description": "وب‌هوک‌های خروجی"},
    {"key": "external_apis", "name": "APIهای خارجی", "category": "integrations", "description": "اتصال به API خارجی"},
    {"key": "ai_provider", "name": "رابط هوش مصنوعی", "category": "integrations", "description": "اتصال به سرویس AI"},
    {"key": "translation", "name": "رابط ترجمه", "category": "integrations", "description": "سرویس ترجمه"},
    {"key": "url_tools", "name": "ابزار URL", "category": "integrations", "description": "ابزارهای لینک"},
    {"key": "notification", "name": "رابط اطلاع‌رسانی", "category": "integrations", "description": "اعلان‌ها"},
    {"key": "custom_webhooks", "name": "وب‌هوک سفارشی", "category": "integrations", "description": "وب‌هوک سفارشی"},
    # ---- advanced ----
    {"key": "multi_account", "name": "چند حساب", "category": "advanced", "description": "مدیریت چند حساب"},
    {"key": "multi_worker", "name": "چند ورکر", "category": "advanced", "description": "چند ورکر هم‌زمان"},
    {"key": "worker_recovery", "name": "بازیابی ورکر", "category": "advanced", "description": "بازیابی خودکار ورکر"},
    {"key": "load_balancing", "name": "توازن بار", "category": "advanced", "description": "توزیع بار بین ورکرها"},
    {"key": "job_queue", "name": "صف کار", "category": "advanced", "description": "صف کارها"},
    {"key": "priority_queue", "name": "صف اولویت", "category": "advanced", "description": "صف با اولویت"},
    {"key": "failover", "name": "جایگزینی", "category": "advanced", "description": "جایگزینی در خطا"},
    {"key": "health_monitoring", "name": "مانیتور سلامت", "category": "advanced", "description": "پایش سلامت"},
    {"key": "remote_config", "name": "پیکربندی راه دور", "category": "advanced", "description": "پیکربندی از راه دور"},
    {"key": "global_kill_switch", "name": "کلید توقف اضطراری", "category": "advanced", "description": "توقف اضطراری همه سلف‌ها"},
]

CATEGORY_NAMES = {
    "message": "💬 پیام",
    "groups": "👥 گروه",
    "channels": "📢 کانال",
    "automation": "🤖 اتوماسیون",
    "media": "🎬 رسانه",
    "search": "🔍 جستجو",
    "entertainment": "🎉 سرگرمی",
    "market": "💰 بازار",
    "plugins": "🧩 پلاگین",
    "system": "⚙️ سیستم",
    "analytics": "📊 تحلیل",
    "security": "🔐 امنیت",
    "integrations": "🔗 یکپارچه‌سازی",
    "advanced": "🚀 پیشرفته",
}
