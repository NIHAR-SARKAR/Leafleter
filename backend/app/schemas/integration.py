"""Integration Pydantic schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IntegrationBase(BaseModel):
    """Base integration fields."""

    integration_type: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    is_active: bool = True
    config: dict[str, Any] | None = None


class IntegrationCreate(IntegrationBase):
    """Integration creation payload.

    ``credentials`` is a write-only plaintext secret that is encrypted at rest.
    """

    credentials: str | None = Field(None, max_length=2000)


class IntegrationUpdate(BaseModel):
    """Integration update payload."""

    name: str | None = Field(None, max_length=255)
    is_active: bool | None = None
    config: dict[str, Any] | None = None
    credentials: str | None = Field(None, max_length=2000)


class IntegrationInDB(IntegrationBase):
    """Integration database response (credentials are never returned)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    created_at: Any
    updated_at: Any


class IntegrationTestResult(BaseModel):
    """Result of testing an integration."""

    success: bool
    message: str
