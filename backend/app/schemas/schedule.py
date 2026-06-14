"""Schedule and job Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScheduleBase(BaseModel):
    """Base schedule fields."""

    name: str = Field(..., max_length=255)
    job_type: str = Field(..., max_length=50)
    cron_expression: str = Field(..., max_length=100)
    timezone: str = "UTC"
    configuration: dict | None = None


class ScheduleCreate(ScheduleBase):
    """Schedule creation payload."""

    topic_id: int | None = None


class ScheduleUpdate(BaseModel):
    """Schedule update payload."""

    name: str | None = Field(None, max_length=255)
    job_type: str | None = Field(None, max_length=50)
    cron_expression: str | None = Field(None, max_length=100)
    timezone: str | None = None
    is_active: bool | None = None
    configuration: dict | None = None


class ScheduleInDB(ScheduleBase):
    """Schedule database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    topic_id: int | None
    organization_id: int
    created_at: datetime
    updated_at: datetime


class JobInDB(BaseModel):
    """Job execution database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_type: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    result_summary: str | None
    error_message: str | None
    schedule_id: int | None
    organization_id: int
    created_at: datetime
