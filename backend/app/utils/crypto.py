"""Symmetric encryption helpers for secrets at rest."""

import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings


def _get_fernet() -> Fernet:
    """Derive a Fernet key from the application secret key."""
    key = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)


def encrypt(value: str) -> str:
    """Encrypt a string and return a URL-safe base64 token."""
    if not value:
        return ""
    f = _get_fernet()
    return f.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    """Decrypt a Fernet token."""
    if not token:
        return ""
    f = _get_fernet()
    return f.decrypt(token.encode("utf-8")).decode("utf-8")
