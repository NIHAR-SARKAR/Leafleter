"""Intelligence ingestion and newsfeed schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IntelligenceItemBase(BaseModel):
    """Base intelligence item fields."""

    item_type: str = Field(..., max_length=50)
    title: str = Field(..., max_length=500)
    content: str | None = Field(None, max_length=20000)
    summary: str | None = Field(None, max_length=2000)
    url: str | None = Field(None, max_length=1000)
    source_name: str | None = Field(None, max_length=255)
    source_url: str | None = Field(None, max_length=1000)
    published_at: datetime | None = None
    relevance_score: float | None = Field(None, ge=0, le=1)
    sentiment: str | None = Field(None, max_length=20)
    tags: list[str] | None = None
    entities: list[dict] | None = None
    extra_metadata: dict | None = None
    is_noise: bool = False


class IntelligenceItemCreate(IntelligenceItemBase):
    """Intelligence item creation payload."""

    content_hash: str = Field(..., max_length=64)


class IntelligenceItemInDB(IntelligenceItemBase):
    """Intelligence item database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    fetched_at: datetime
    content_hash: str
    organization_id: int
    source_id: int | None
    competitor_id: int | None
    topic_id: int | None
    created_at: datetime
    updated_at: datetime


class IntelligenceItemFilter(BaseModel):
    """Filter parameters for the newsfeed."""

    item_type: str | None = Field(None, max_length=50)
    competitor_id: int | None = None
    topic_id: int | None = None
    sentiment: str | None = Field(None, max_length=20)
    tag: str | None = Field(None, max_length=100)
    is_noise: bool = False


class IntelligenceSourceBase(BaseModel):
    """Base intelligence source fields."""

    source_type: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    url: str | None = Field(None, max_length=1000)
    query: str | None = Field(None, max_length=1000)
    configuration: dict | None = None
    refresh_interval_minutes: int | None = Field(None, ge=1)
    is_active: bool = True
    competitor_id: int | None = None
    topic_id: int | None = None


class IntelligenceSourceCreate(IntelligenceSourceBase):
    """Intelligence source creation payload."""

    pass


class IntelligenceSourceUpdate(BaseModel):
    """Intelligence source update payload."""

    name: str | None = Field(None, max_length=255)
    url: str | None = Field(None, max_length=1000)
    query: str | None = Field(None, max_length=1000)
    configuration: dict | None = None
    refresh_interval_minutes: int | None = Field(None, ge=1)
    is_active: bool | None = None


class IntelligenceSourceInDB(IntelligenceSourceBase):
    """Intelligence source database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    fetch_error: str | None = None
    last_fetched_at: datetime | None = None
    organization_id: int
    created_at: datetime
    updated_at: datetime


class IntelligenceIngestResult(BaseModel):
    """Result of an ingestion run for a source."""

    source_id: int
    items_fetched: int
    items_stored: int
    items_deduplicated: int
    items_filtered: int
    error: str | None = None
