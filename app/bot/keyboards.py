"""Inline keyboard builders (Persian labels)."""

from __future__ import annotations

from telethon import Button


def main_panel() -> list:
    return [
        [Button.inline("🤖 مدیریت سلف", b"ub"), Button.inline("🧩 قابلیت‌ها", b"modules")],
        [Button.inline("🤖 اتوماسیون", b"automation"), Button.inline("⏰ زمان‌بندی", b"scheduler")],
        [Button.inline("📊 آمار", b"stats"), Button.inline("⚙️ تنظیمات", b"settings")],
        [Button.inline("💳 اشتراک", b"subscription"), Button.inline("🆘 پشتیبانی", b"support")],
    ]


def account_panel() -> list:
    return [[Button.inline("🔙 بازگشت", b"back_panel")]]


def subscription_panel() -> list:
    return [
        [Button.inline("💳 خرید اشتراک", b"buy_plan")],
        [Button.inline("🔙 بازگشت", b"back_panel")],
    ]


def userbot_panel(has_account: bool) -> list:
    rows = []
    if not has_account:
        rows.append([Button.inline("🔗 اتصال حساب تلگرام", b"auth_start")])
    else:
        rows.append([Button.inline("🔄 اتصال مجدد", b"auth_start")])
    rows.append([Button.inline("🔙 بازگشت", b"back_panel")])
    return rows


def plans_keyboard(plans: list) -> list:
    rows = []
    for plan in plans:
        rows.append([Button.inline(f"💎 {plan.name}", f"plan:{plan.id}".encode())])
    rows.append([Button.inline("🔙 بازگشت", b"back_panel")])
    return rows


def plan_detail(plan_id: int) -> list:
    return [
        [Button.inline("💳 پرداخت", f"pay:{plan_id}".encode())],
        [Button.inline("🔙 بازگشت", b"back_panel")],
    ]


def cancel() -> list:
    return [[Button.inline("❌ لغو", b"cancel")]]


def back_panel() -> list:
    return [[Button.inline("🔙 بازگشت", b"back_panel")]]
