"""Job execution Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobBase(BaseModel):
    """Base job fields."""

    job_type: str
    status: str = "pending"
    result_summary: str | None = None
    error_message: str | None = None


class JobCreate(JobBase):
    """Job creation payload."""

    organization_id: int
    schedule_id: int | None = None


class JobInDB(JobBase):
    """Job database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    schedule_id: int | None
    organization_id: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
