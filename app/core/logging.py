"""Structured logging with sensitive-data redaction.

Never logs: Telegram verification codes, 2FA passwords, raw sessions,
api_hash, bot tokens or encryption keys.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone

# Keys whose values must be redacted if they appear in structured records.
_SENSITIVE_KEYS = {
    "password",
    "2fa_password",
    "code",
    "verification_code",
    "session",
    "session_str",
    "string_session",
    "api_hash",
    "bot_token",
    "token",
    "encryption_key",
    "phone_code_hash",
    "authorization",
}

# Coarse patterns for values that look like secrets inside a formatted message.
_PATTERNS = [
    # Telethon session strings start with a digit and are very long.
    re.compile(r"\b\d[A-Za-z0-9_\-]{200,}\b"),
    # Long hex signatures.
    re.compile(r"\b[0-9a-fA-F]{64,}\b"),
]

_REDACTED = "***REDACTED***"


def redact_text(value: str) -> str:
    """Redact obvious secrets from a plain message string."""
    for pattern in _PATTERNS:
        value = pattern.sub(_REDACTED, value)
    return value


def _redact_mapping(mapping: dict) -> dict:
    out: dict = {}
    for key, val in mapping.items():
        if isinstance(val, dict):
            out[key] = _redact_mapping(val)
        elif isinstance(val, (list, tuple)):
            out[key] = [_redact_mapping(v) if isinstance(v, dict) else v for v in val]
        elif key.lower() in _SENSITIVE_KEYS:
            out[key] = _REDACTED
        else:
            out[key] = val
    return out


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log record."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_text(record.getMessage()),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(_redact_mapping(extra))
        return json.dumps(payload, ensure_ascii=False, default=str)


class SensitiveFilter(logging.Filter):
    """Defense-in-depth: strip sensitive key/values from any record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if getattr(record, "args", None):
            record.args = tuple(
                _redact_mapping(a) if isinstance(a, dict) else a for a in record.args
            )
        return True


class JsonLogger(logging.Logger):
    """Logger that accepts an ``extra_fields`` kwarg for structured metadata.

    Usage: ``log.info("message", extra_fields={"key": "value"})``.
    """

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1, **kwargs):
        extra_fields = kwargs.pop("extra_fields", None)
        if extra_fields is not None:
            extra = dict(extra or {})
            extra["extra_fields"] = extra_fields
        super()._log(
            level,
            msg,
            args,
            exc_info=exc_info,
            extra=extra,
            stack_info=stack_info,
            stacklevel=stacklevel,
        )


def configure_logging(level: str = "INFO", debug: bool = False) -> None:
    """Configure the root logger for structured JSON output."""
    logging.setLoggerClass(JsonLogger)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(SensitiveFilter())
    root.addHandler(handler)

    # Quiet noisy third-party loggers.
    for noisy in ("asyncio", "telethon.network", "aiosqlite"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


class _ExtraFieldsAdapter(logging.LoggerAdapter):
    """Adapts a standard logger to accept ``extra_fields`` at any call site."""

    def process(self, msg, kwargs):
        extra_fields = kwargs.pop("extra_fields", None)
        if extra_fields is not None:
            extra = dict(kwargs.get("extra") or {})
            extra["extra_fields"] = extra_fields
            kwargs["extra"] = extra
        return msg, kwargs


def get_logger(name: str) -> logging.LoggerAdapter:
    """Return a logger that supports ``extra_fields`` structured metadata."""
    return _ExtraFieldsAdapter(logging.getLogger(name), {})
