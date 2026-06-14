"""Lightweight Fernet encryption for provider API keys."""

import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings


def _get_fernet() -> Fernet:
    """Derive a stable Fernet key from the application secret."""
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_api_key(plain_key: str | None) -> str | None:
    """Encrypt a plain API key."""
    if plain_key is None:
        return None
    return _get_fernet().encrypt(plain_key.encode("utf-8")).decode("utf-8")


def decrypt_api_key(encrypted_key: str | None) -> str | None:
    """Decrypt an encrypted API key."""
    if encrypted_key is None:
        return None
    return _get_fernet().decrypt(encrypted_key.encode("utf-8")).decode("utf-8")
