"""User Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.organization import OrganizationShort
from app.schemas.role import RoleShort


class UserBase(BaseModel):
    """Base user fields."""

    email: EmailStr
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    is_active: bool = True
    timezone: str = "UTC"
    locale: str = "en"


class UserCreate(UserBase):
    """User registration payload."""

    password: str = Field(..., min_length=8, max_length=128)
    organization_name: str | None = Field(None, max_length=255)
    role_id: int | None = None


class UserCreateInternal(UserBase):
    """Internal user creation payload with hashed password."""

    hashed_password: str
    organization_id: int
    role_id: int | None = None
    is_superuser: bool = False


class UserUpdate(BaseModel):
    """User update payload."""

    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    is_active: bool | None = None
    timezone: str | None = None
    locale: str | None = None
    role_id: int | None = None
    avatar_url: str | None = Field(None, max_length=500)


class UserInDB(UserBase):
    """User response from database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_superuser: bool
    is_email_verified: bool
    last_login_at: datetime | None
    organization_id: int
    role_id: int | None
    created_at: datetime
    updated_at: datetime


class UserPublic(UserInDB):
    """Public user response with related data."""

    organization: OrganizationShort | None = None
    role: RoleShort | None = None
    full_name: str


class UserShort(BaseModel):
    """Compact user reference."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str


class UserLogin(BaseModel):
    """User login payload."""

    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    """Password reset request payload."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation payload."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
