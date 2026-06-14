"""API key Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class APIKeyCreate(BaseModel):
    """API key creation payload."""

    name: str = Field(..., max_length=100)
    scopes: list[str] | None = None
    expires_at: datetime | None = None


class APIKeyUpdate(BaseModel):
    """API key update payload."""

    name: str | None = Field(None, max_length=100)
    is_active: bool | None = None
    scopes: list[str] | None = None


class APIKeyInDB(BaseModel):
    """API key database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    key_prefix: str
    is_active: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    scopes: str | None
    created_at: datetime


class APIKeyPublic(APIKeyInDB):
    """Public API key response with plaintext key shown once."""

    plain_key: str | None = None
