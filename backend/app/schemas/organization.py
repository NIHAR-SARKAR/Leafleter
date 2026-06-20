"""Organization Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrganizationBase(BaseModel):
    """Base organization fields."""

    name: str = Field(..., max_length=255)
    description: str | None = Field(None, max_length=2000)
    billing_email: str | None = Field(None, max_length=255)
    plan: str = "free"


class OrganizationCreate(OrganizationBase):
    """Organization creation payload."""

    slug: str | None = Field(None, max_length=255)


class OrganizationUpdate(BaseModel):
    """Organization update payload."""

    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=2000)
    billing_email: str | None = Field(None, max_length=255)
    plan: str | None = None
    settings: dict | None = None
    features: list[dict] | None = None
    is_active: bool | None = None


class OrganizationBranding(BaseModel):
    """White-label branding payload."""

    branding_primary_color: str | None = Field(None, max_length=7)
    branding_logo_url: str | None = Field(None, max_length=500)
    branding_favicon_url: str | None = Field(None, max_length=500)
    custom_domain: str | None = Field(None, max_length=255)


class OrganizationInDB(OrganizationBase):
    """Organization database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: str
    slug: str
    is_active: bool
    is_white_label: bool
    features: list[dict] | None = None
    created_at: datetime
    updated_at: datetime


class OrganizationPublic(OrganizationInDB):
    """Public organization response."""

    branding_primary_color: str | None
    branding_logo_url: str | None
    branding_favicon_url: str | None
    custom_domain: str | None


class OrganizationShort(BaseModel):
    """Compact organization reference."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
