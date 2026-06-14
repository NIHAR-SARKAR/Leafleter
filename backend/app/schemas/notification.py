"""Notification Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    """Notification creation payload."""

    channel: str = Field(..., max_length=50)
    recipient: str = Field(..., max_length=255)
    subject: str | None = Field(None, max_length=255)
    body: str | None = Field(None, max_length=10000)
    metadata: dict[str, Any] | None = None


class NotificationUpdate(BaseModel):
    """Notification update payload."""

    is_read: bool | None = None


class NotificationInDB(BaseModel):
    """Notification database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    channel: str
    recipient: str
    subject: str | None
    body: str | None
    status: str
    is_read: bool
    sent_at: datetime | None
    delivered_at: datetime | None
    error_message: str | None
    user_id: int | None
    organization_id: int
    created_at: datetime
