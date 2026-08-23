"""Permission codes and default role assignments (RBAC).

Roles: OWNER, SUPER_ADMIN, ADMIN, MODERATOR, SUPPORT.
"""

from __future__ import annotations


class Permissions:
    """String constants for every admin permission."""

    USERS_VIEW = "users.view"
    USERS_EDIT = "users.edit"
    USERS_SUSPEND = "users.suspend"

    PAYMENTS_VIEW = "payments.view"
    PAYMENTS_APPROVE = "payments.approve"
    PAYMENTS_REJECT = "payments.reject"

    SUBSCRIPTIONS_VIEW = "subscriptions.view"
    SUBSCRIPTIONS_EDIT = "subscriptions.edit"

    USERBOTS_VIEW = "userbots.view"
    USERBOTS_START = "userbots.start"
    USERBOTS_STOP = "userbots.stop"
    USERBOTS_RESTART = "userbots.restart"

    MODULES_VIEW = "modules.view"
    MODULES_MANAGE = "modules.manage"

    LOGS_VIEW = "logs.view"

    SETTINGS_VIEW = "settings.view"
    SETTINGS_EDIT = "settings.edit"

    BROADCAST_SEND = "broadcast.send"

    ADMINS_MANAGE = "admins.manage"

    SUPPORT_MANAGE = "support.manage"

    # Privacy-sensitive: message content access (off by default).
    MESSAGES_VIEW = "messages.view"


ALL_PERMISSIONS: tuple[str, ...] = tuple(
    sorted(
        {
            Permissions.USERS_VIEW,
            Permissions.USERS_EDIT,
            Permissions.USERS_SUSPEND,
            Permissions.PAYMENTS_VIEW,
            Permissions.PAYMENTS_APPROVE,
            Permissions.PAYMENTS_REJECT,
            Permissions.SUBSCRIPTIONS_VIEW,
            Permissions.SUBSCRIPTIONS_EDIT,
            Permissions.USERBOTS_VIEW,
            Permissions.USERBOTS_START,
            Permissions.USERBOTS_STOP,
            Permissions.USERBOTS_RESTART,
            Permissions.MODULES_VIEW,
            Permissions.MODULES_MANAGE,
            Permissions.LOGS_VIEW,
            Permissions.SETTINGS_VIEW,
            Permissions.SETTINGS_EDIT,
            Permissions.BROADCAST_SEND,
            Permissions.ADMINS_MANAGE,
            Permissions.SUPPORT_MANAGE,
            Permissions.MESSAGES_VIEW,
        }
    )
)


# Default role -> permission set. OWNER gets everything (computed at seed time).
DEFAULT_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "SUPER_ADMIN": {
        Permissions.USERS_VIEW,
        Permissions.USERS_EDIT,
        Permissions.USERS_SUSPEND,
        Permissions.PAYMENTS_VIEW,
        Permissions.PAYMENTS_APPROVE,
        Permissions.PAYMENTS_REJECT,
        Permissions.SUBSCRIPTIONS_VIEW,
        Permissions.SUBSCRIPTIONS_EDIT,
        Permissions.USERBOTS_VIEW,
        Permissions.USERBOTS_START,
        Permissions.USERBOTS_STOP,
        Permissions.USERBOTS_RESTART,
        Permissions.MODULES_VIEW,
        Permissions.MODULES_MANAGE,
        Permissions.LOGS_VIEW,
        Permissions.SETTINGS_VIEW,
        Permissions.SETTINGS_EDIT,
        Permissions.BROADCAST_SEND,
        Permissions.ADMINS_MANAGE,
        Permissions.SUPPORT_MANAGE,
    },
    "ADMIN": {
        Permissions.USERS_VIEW,
        Permissions.USERS_EDIT,
        Permissions.PAYMENTS_VIEW,
        Permissions.PAYMENTS_APPROVE,
        Permissions.PAYMENTS_REJECT,
        Permissions.SUBSCRIPTIONS_VIEW,
        Permissions.USERBOTS_VIEW,
        Permissions.USERBOTS_START,
        Permissions.USERBOTS_STOP,
        Permissions.USERBOTS_RESTART,
        Permissions.MODULES_VIEW,
        Permissions.LOGS_VIEW,
        Permissions.SETTINGS_VIEW,
        Permissions.SUPPORT_MANAGE,
    },
    "MODERATOR": {
        Permissions.USERS_VIEW,
        Permissions.SUPPORT_MANAGE,
    },
    "SUPPORT": {
        Permissions.SUBSCRIPTIONS_VIEW,
        Permissions.SUPPORT_MANAGE,
    },
}

ROLE_NAMES: tuple[str, ...] = ("OWNER", "SUPER_ADMIN", "ADMIN", "MODERATOR", "SUPPORT")
