"""Symmetric encryption utilities for sensitive provider credentials."""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.core.exceptions import AppException


def _fernet() -> Fernet:
    """Build a Fernet instance from the configured secret key."""
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_text(plain_text: str) -> str:
    """Encrypt a plaintext string."""
    return _fernet().encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_text(cipher_text: str) -> str:
    """Decrypt a string previously encrypted with :func:`encrypt_text`."""
    try:
        return _fernet().decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise AppException("Failed to decrypt credential") from exc
