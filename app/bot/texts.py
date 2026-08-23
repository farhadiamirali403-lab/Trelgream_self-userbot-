"""Persian UI strings for the central bot."""

from __future__ import annotations

START = (
    "🤖 به <b>ربات شخصی تلگرام</b> خوش آمدید!\n\n"
    "✨ امکانات:\n"
    "• 🔗 اتصال حساب تلگرام\n"
    "• ⚙️ بیش از ۴۰ قابلیت خودکار\n"
    "• 🤖 اجرای سلف اختصاصی\n"
    "• 💎 اشتراک با پلن‌های متنوع\n\n"
    "برای شروع از منوی زیر استفاده کنید 👇"
)

HELP = (
    "📖 راهنمای دستورات\n\n"
    "/start — شروع و ثبت‌نام\n"
    "/panel — پنل کاربری\n"
    "/account — حساب کاربری\n"
    "/subscription — اشتراک\n"
    "/userbot — ربات شخصی\n"
    "/settings — تنظیمات\n"
    "/support — پشتیبانی\n"
    "/admin — پنل ادمین (فقط ادمین‌ها)"
)

MAIN_PANEL = (
    "━━━━━━━━━━━━━━━\n"
    "🤖 پنل مدیریت سلف\n"
    "━━━━━━━━━━━━━━━\n\n"
    "👤 حساب: {account}\n"
    "💎 اشتراک: {plan}\n"
    "📅 انقضا: {expiry}\n"
    "🤖 سلف: {userbot}\n"
)

ACCOUNT_INFO = (
    "👤 حساب کاربری\n\n"
    "شناسه: {id}\n"
    "یوزرنیم: @{username}\n"
    "تلفن: {phone}\n"
    "وضعیت: {status}\n"
)

SUBSCRIPTION_INFO = (
    "💎 اشتراک\n\n"
    "پلن: {plan}\n"
    "وضعیت: {status}\n"
    "شروع: {started}\n"
    "انقضا: {expires}\n"
)

NO_SUBSCRIPTION = "💎 شما اشتراک فعالی ندارید.\nبرای فعال‌سازی یکی از پلن‌ها را انتخاب کنید."

PLAN_LINE = "▫️ {name} — {price:,} تومان / {days} روز\n"
PLAN_DETAIL = (
    "💎 {name}\n\n"
    "{description}\n\n"
    "💰 قیمت: {price:,} تومان\n"
    "📅 مدت: {days} روز\n"
    "🤖 حداکثر سلف: {userbots}\n"
    "🧩 حداکثر ماژول: {modules}\n"
)

PAYMENT_CARD = (
    "💳 پرداخت کارت به کارت\n\n"
    "لطفاً مبلغ <b>{amount:,} تومان</b> را به کارت زیر واریز کنید:\n\n"
    "<code>{card_number}</code>\n"
    "به نام: {card_owner}\n\n"
    "سپس تصویر یا فایل رسید را ارسال کنید."
)

PAYMENT_SUBMITTED = "✅ رسید شما ثبت شد و در انتظار بررسی است.\nشناسه پرداخت: <code>{reference}</code>"

USERBOT_INFO = (
    "🤖 ربات شخصی شما\n\n"
    "وضعیت: {status}\n"
    "آخرین فعالیت: {heartbeat}\n"
)

USERBOT_STATUS_EMOJI = {
    "RUNNING": "🟢 آنلاین",
    "STARTING": "🟡 در حال شروع",
    "STOPPED": "🔴 خاموش",
    "STOPPING": "🟠 در حال توقف",
    "ERROR": "⚠️ خطا",
    "RECOVERING": "🔄 در حال بازیابی",
    "SUSPENDED": "⏸ معلق",
    "AUTHORIZED": "✅ متصل (آماده شروع)",
    "CREATED": "⚪️ ساخته شده",
}

SUBSCRIPTION_STATUS = {
    "active": "فعال ✅",
    "pending": "در انتظار پرداخت ⏳",
    "expired": "منقضی شده ❌",
    "suspended": "معلق ⏸",
    "cancelled": "لغو شده 🚫",
}

ACCOUNT_STATUS = {
    True: "فعال",
    False: "غیرفعال",
}

ASK_PHONE = "📱 لطفاً شماره تلفن حساب تلگرام خود را با کد کشور ارسال کنید.\nمثال: <code>+989xxxxxxxxx</code>"
AUTH_WEB_LINK = (
    "🔗 برای اتصال حساب تلگرام، این آدرس را در مرورگر کامپیوتر خود باز کنید:\n\n"
    "<code>{link}</code>\n\n"
    "کد تأیید را در صفحه وب وارد کنید (نه اینجا)."
)
ASK_CODE = "{message}\n\nلطفاً کد تأیید را ارسال کنید."
ASK_2FA = "🔐 این حساب رمز دومرحله‌ای (2FA) دارد.\nلطفاً رمز 2FA خود را ارسال کنید."
AUTH_SUCCESS = "✅ احراز هویت با موفقیت انجام شد!"
AUTH_CANCELLED = "❌ عملیات لغو شد."

SETTINGS_INFO = "⚙️ تنظیمات\n\nبه‌زودی تنظیمات بیشتری اضافه می‌شود."
SUPPORT_INFO = "🆘 پشتیبانی\n\nبرای ارتباط با پشتیبانی پیام خود را ارسال کنید."
NOT_AUTHORIZED = "⚠️ هنوز حسابی به پلتفرم متصل نکرده‌اید."
