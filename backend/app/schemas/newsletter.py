"""Newsletter Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NewsletterIssueBase(BaseModel):
    """Base newsletter issue fields."""

    schedule_id: int | None = None
    title: str = Field(..., max_length=255)
    content_markdown: str
    content_html: str | None = None
    status: str = "pending"
    recipient_count: int | None = None


class NewsletterIssueCreate(BaseModel):
    """Payload to generate a new newsletter issue."""

    title: str | None = Field(None, max_length=255)
    integration_ids: list[int] = Field(default_factory=list)
    email_recipients: list[str] = Field(default_factory=list)
    topic_ids: list[int] = Field(default_factory=list)
    competitor_ids: list[int] = Field(default_factory=list)
    since_hours: int = Field(default=24, ge=1, le=720)
    send_now: bool = False


class NewsletterIssueInDB(NewsletterIssueBase):
    """Newsletter issue database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sent_at: datetime | None
    organization_id: int
    created_at: datetime
    updated_at: datetime


class NewsletterSendRequest(BaseModel):
    """Payload to send an existing newsletter issue."""

    integration_ids: list[int] = Field(default_factory=list)
    email_recipients: list[str] = Field(default_factory=list)


class NewsletterScheduleSummary(BaseModel):
    """Lightweight schedule summary used by the newsletter UI."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    cron_expression: str
    timezone: str
    is_active: bool
    configuration: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
