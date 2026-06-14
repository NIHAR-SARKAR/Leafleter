"""Topic workspace Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TopicSourceBase(BaseModel):
    """Base topic source fields."""

    source_type: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    url: str | None = Field(None, max_length=1000)
    query: str | None = Field(None, max_length=5000)
    platform: str | None = Field(None, max_length=50)
    account_id: str | None = Field(None, max_length=255)
    configuration: dict | None = None


class TopicSourceCreate(TopicSourceBase):
    """Topic source creation payload."""

    pass


class TopicSourceUpdate(BaseModel):
    """Topic source update payload."""

    name: str | None = Field(None, max_length=255)
    url: str | None = Field(None, max_length=1000)
    query: str | None = Field(None, max_length=5000)
    platform: str | None = Field(None, max_length=50)
    account_id: str | None = Field(None, max_length=255)
    configuration: dict | None = None
    fetch_status: str | None = Field(None, max_length=50)


class TopicSourceInDB(TopicSourceBase):
    """Topic source database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    last_fetched_at: datetime | None
    fetch_status: str
    fetch_error: str | None
    raw_data: str | None
    created_at: datetime
    updated_at: datetime


class TopicBase(BaseModel):
    """Base topic fields."""

    name: str = Field(..., max_length=255)
    description: str | None = Field(None, max_length=2000)
    keywords: str | None = Field(None, max_length=2000)
    configuration: dict | None = None
    is_public: bool = False


class TopicCreate(TopicBase):
    """Topic creation payload."""

    pass


class TopicUpdate(BaseModel):
    """Topic update payload."""

    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=2000)
    keywords: str | None = Field(None, max_length=2000)
    configuration: dict | None = None
    is_public: bool | None = None
    status: str | None = Field(None, max_length=50)


class TopicInDB(TopicBase):
    """Topic database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    organization_id: int
    created_by_user_id: int | None
    created_at: datetime
    updated_at: datetime


class TopicPublic(TopicInDB):
    """Public topic response with sources."""

    sources: list[TopicSourceInDB]


class TopicShort(BaseModel):
    """Compact topic reference."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str


class AnalysisResultInDB(BaseModel):
    """Analysis result database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    result_type: str
    score: float | None
    summary: str | None
    details: dict | None
    raw_output: str | None
    run_id: int
    created_at: datetime


class AnalysisRunInDB(BaseModel):
    """Analysis run database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_type: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    input_tokens: int
    output_tokens: int
    cost: float
    configuration: dict | None
    topic_id: int
    provider_id: int | None
    created_at: datetime
    results: list[AnalysisResultInDB]


class TopicAnalyzeRequest(BaseModel):
    """Request to run analysis on a topic."""

    analysis_types: list[str] = Field(default_factory=lambda: ["sentiment"])
    provider_id: int | None = None
    model: str | None = Field(None, max_length=100)
