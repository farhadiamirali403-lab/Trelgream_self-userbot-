"""Cryptographic primitives: session encryption, password hashing, command signing."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from typing import Protocol

from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken

from app.core.exceptions import SessionError

_argon2 = Argon2Hasher(time_cost=3, memory_cost=65536, parallelism=2)


def generate_fernet_key() -> str:
    """Return a fresh Fernet key (used to seed SESSION_ENCRYPTION_KEY)."""
    return Fernet.generate_key().decode()


class SessionCipher:
    """Encrypt/decrypt Telegram session strings at rest (Fernet / AES128-CBC-HMAC)."""

    def __init__(self, key: str) -> None:
        if not key:
            raise SessionError("SESSION_ENCRYPTION_KEY تنظیم نشده است")
        self._fernet = Fernet(self._normalize_key(key))

    @staticmethod
    def _normalize_key(key: str) -> bytes:
        """Accept either a real Fernet key or an arbitrary passphrase."""
        try:
            Fernet(key.encode())
            return key.encode()
        except (ValueError, TypeError):
            digest = hashlib.sha256(key.encode("utf-8")).digest()
            return base64.urlsafe_b64encode(digest)

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            raise SessionError("session خالی قابل رمزنگاری نیست")
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")

    def decrypt(self, token: str) -> str:
        try:
            return self._fernet.decrypt(token.encode("ascii")).decode("utf-8")
        except (InvalidToken, ValueError) as exc:  # pragma: no cover - defensive
            raise SessionError("رمزگشایی نشست ناموفق بود") from exc


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, hashed: str) -> bool: ...


class Argon2PasswordHasher:
    """Argon2id password hashing (CPU-bound; call via ``asyncio.to_thread``)."""

    def hash(self, password: str) -> str:
        return _argon2.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        try:
            return _argon2.verify(hashed, password)
        except (VerifyMismatchError, Exception):  # noqa: BLE001 - return False on any mismatch
            return False


class CommandSigner:
    """HMAC-SHA256 signing for signed internal commands (replay/forgery protection)."""

    def __init__(self, secret: str) -> None:
        self._secret = secret.encode("utf-8")

    def sign(self, payload: str) -> str:
        return hmac.new(self._secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify(self, payload: str, signature: str) -> bool:
        return hmac.compare_digest(self.sign(payload), signature)


def new_secret_token(nbytes: int = 32) -> str:
    """Generate a URL-safe random token."""
    return secrets.token_urlsafe(nbytes)
