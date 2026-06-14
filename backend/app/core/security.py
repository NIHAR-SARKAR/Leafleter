"""Security utilities for password hashing, JWT tokens, and API keys."""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.token import TokenPayload


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    plain_bytes = plain_password.encode("utf-8")
    hash_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(plain_bytes, hash_bytes)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str | Any) -> str:
    """Create a signed JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        token_type = payload.get("type")
        if sub is None:
            raise ValueError("Token missing subject")
        return TokenPayload(sub=sub, type=token_type, exp=payload.get("exp"))
    except (JWTError, ValidationError) as exc:
        raise ValueError("Invalid token") from exc


def generate_api_key() -> tuple[str, str]:
    """Generate a plaintext API key and its hashed secret.

    Returns:
        A tuple of (prefixed_plain_key, hashed_key).
    """
    raw = secrets.token_urlsafe(32)
    plain_key = f"mm_{raw}"
    hashed_key = hash_api_key(plain_key)
    return plain_key, hashed_key


def hash_api_key(plain_key: str) -> str:
    """Hash an API key for storage."""
    return bcrypt.hashpw(plain_key.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its stored hash."""
    return bcrypt.checkpw(plain_key.encode("utf-8"), hashed_key.encode("utf-8"))


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)
