"""Competitor Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompetitorSnapshotBase(BaseModel):
    """Base competitor snapshot fields."""

    snapshot_type: str = Field(..., max_length=50)
    source_url: str | None = Field(None, max_length=500)
    content: str | None = Field(None, max_length=20000)
    metrics: dict | None = None
    changes: str | None = Field(None, max_length=5000)


class CompetitorSnapshotCreate(CompetitorSnapshotBase):
    """Competitor snapshot creation payload."""

    pass


class CompetitorSnapshotInDB(CompetitorSnapshotBase):
    """Competitor snapshot database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    competitor_id: int
    created_at: datetime


class CompetitorBase(BaseModel):
    """Base competitor fields."""

    name: str = Field(..., max_length=255)
    website_url: str | None = Field(None, max_length=500)
    industry: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=2000)
    social_handles: str | None = Field(None, max_length=1000)
    watch_config: dict | None = None


class CompetitorCreate(CompetitorBase):
    """Competitor creation payload."""

    pass


class CompetitorUpdate(BaseModel):
    """Competitor update payload."""

    name: str | None = Field(None, max_length=255)
    website_url: str | None = Field(None, max_length=500)
    industry: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=2000)
    social_handles: str | None = Field(None, max_length=1000)
    watch_config: dict | None = None
    is_active: bool | None = None


class CompetitorInDB(CompetitorBase):
    """Competitor database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    organization_id: int
    created_at: datetime
    updated_at: datetime


class CompetitorPublic(CompetitorInDB):
    """Public competitor with snapshots."""

    snapshots: list[CompetitorSnapshotInDB]
