"""Encryption at rest for secrets that live in the database — currently only
Apprise notification URLs, which frequently embed webhook tokens or SMTP
passwords (e.g. ``mailto://user:password@...``, ``slack://TokenA/TokenB/...``).

Never log or return a decrypted value through the API after creation; the
alert channel API only ever exposes a masked preview.
"""

from __future__ import annotations

from cryptography.fernet import Fernet

from app.core.config import settings

_fernet = Fernet(settings.encryption_key.encode())


def encrypt(value: str) -> bytes:
    return _fernet.encrypt(value.encode())


def decrypt(value: bytes) -> str:
    return _fernet.decrypt(value).decode()


def mask(value: str) -> str:
    """A safe-to-display preview, e.g. 'slack://***...tps5'."""
    scheme, _, rest = value.partition("://")
    if not rest:
        return "***"
    tail = rest[-4:] if len(rest) > 4 else "***"
    return f"{scheme}://***{tail}"
