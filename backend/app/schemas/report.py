"""Report Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ReportBase(BaseModel):
    """Base report fields."""

    title: str = Field(..., max_length=255)
    report_type: str = Field(..., max_length=50)
    format: str = Field(..., max_length=20)
    template: str | None = Field(None, max_length=100)
    configuration: dict | None = None


class ReportCreate(ReportBase):
    """Report creation payload."""

    topic_id: int


class ReportUpdate(BaseModel):
    """Report update payload."""

    title: str | None = Field(None, max_length=255)
    is_approved: bool | None = None


class ReportInDB(ReportBase):
    """Report database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    file_path: str | None
    file_size: int | None
    download_url: str | None
    is_approved: bool
    topic_id: int
    organization_id: int
    approved_by_user_id: int | None
    created_at: datetime
    updated_at: datetime


class ReportPublic(ReportInDB):
    """Public report response."""

    topic: Any | None = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
