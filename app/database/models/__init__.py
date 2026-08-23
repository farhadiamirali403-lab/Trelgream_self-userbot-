"""Import all models so Alembic autogenerate and Base.metadata can see them."""

from app.database.models.admins import Admin, AdminRole, Permission, Role, RolePermission
from app.database.models.analytics import UsageMetric
from app.database.models.audit import AuditLog, ErrorLog, SystemLog
from app.database.models.automation import AutomationAction, AutomationCondition, AutomationRule
from app.database.models.billing import Payment, PaymentReceipt, Plan, Subscription
from app.database.models.modules import Module, ModuleSetting, UserModule
from app.database.models.scheduler import ScheduledTask
from app.database.models.settings import PaymentSetting, Setting
from app.database.models.support import Notification, SupportTicket
from app.database.models.telegram import TelegramAccount, TelegramSession
from app.database.models.userbots import Userbot
from app.database.models.users import User
from app.database.models.workers import Worker, WorkerHeartbeat

__all__ = [
    "Admin",
    "AdminRole",
    "Permission",
    "Role",
    "RolePermission",
    "UsageMetric",
    "AuditLog",
    "ErrorLog",
    "SystemLog",
    "AutomationAction",
    "AutomationCondition",
    "AutomationRule",
    "Payment",
    "PaymentReceipt",
    "Plan",
    "Subscription",
    "Module",
    "ModuleSetting",
    "UserModule",
    "ScheduledTask",
    "PaymentSetting",
    "Setting",
    "Notification",
    "SupportTicket",
    "TelegramAccount",
    "TelegramSession",
    "Userbot",
    "User",
    "Worker",
    "WorkerHeartbeat",
]
