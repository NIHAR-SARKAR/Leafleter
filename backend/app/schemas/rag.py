"""RAG / Ask Comrade schemas."""

from pydantic import BaseModel, ConfigDict, Field


class VectorChunkCreate(BaseModel):
    """Vector chunk creation payload."""

    chunk_type: str = Field(..., max_length=50)
    source_id: int
    content: str = Field(..., max_length=10000)
    embedding: list[float] | None = None
    embedding_model: str | None = Field(None, max_length=100)
    token_count: int | None = None
    extra_metadata: dict | None = None


class VectorChunkInDB(VectorChunkCreate):
    """Vector chunk database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int


class AskRequest(BaseModel):
    """Ask Comrade request payload."""

    question: str = Field(..., max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict | None = None
    provider_id: int | None = Field(default=None, ge=1)


class AskSource(BaseModel):
    """Source citation for an Ask Comrade answer."""

    chunk_type: str
    title: str | None = None
    url: str | None = None
    content: str | None = None
    score: float | None = None


class AskResponse(BaseModel):
    """Ask Comrade response."""

    question: str
    answer: str
    sources: list[AskSource]
