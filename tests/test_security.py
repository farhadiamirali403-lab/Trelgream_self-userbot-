"""Security primitives tests."""

from __future__ import annotations

import pytest

from app.core.exceptions import SessionError
from app.core.security import (
    Argon2PasswordHasher,
    CommandSigner,
    SessionCipher,
    generate_fernet_key,
)


def test_session_cipher_roundtrip():
    cipher = SessionCipher(generate_fernet_key())
    token = cipher.encrypt("1BQANOTEuM...raw_session_string...")
    assert cipher.decrypt(token) == "1BQANOTEuM...raw_session_string..."


def test_session_cipher_accepts_passphrase():
    cipher = SessionCipher("my-passphrase")
    token = cipher.encrypt("secret-session")
    assert cipher.decrypt(token) == "secret-session"


def test_session_cipher_rejects_empty():
    with pytest.raises(SessionError):
        SessionCipher("")


def test_session_cipher_decrypt_failure():
    cipher = SessionCipher(generate_fernet_key())
    with pytest.raises(SessionError):
        cipher.decrypt("not-a-valid-token")


def test_password_hasher():
    hasher = Argon2PasswordHasher()
    hashed = hasher.hash("s3cret-pass")
    assert hasher.verify("s3cret-pass", hashed)
    assert not hasher.verify("wrong-pass", hashed)


def test_command_signer_verify():
    signer = CommandSigner("internal-secret")
    sig = signer.sign("payload")
    assert signer.verify("payload", sig)
    assert not signer.verify("tampered", sig)
