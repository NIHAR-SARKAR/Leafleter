"""Fact extraction and insight schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FactEvidence(BaseModel):
    """Evidence backing a fact."""

    source_name: str | None = None
    url: str | None = None
    quote: str | None = None


class FactTemplateBase(BaseModel):
    """Base fact template fields."""

    fact_type: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: str | None = Field(None, max_length=2000)
    prompt: str | None = Field(None, max_length=10000)
    schema_definition: dict | None = None
    example: dict | None = None
    is_active: bool = True


class FactTemplateCreate(FactTemplateBase):
    """Fact template creation payload."""

    pass


class FactTemplateUpdate(BaseModel):
    """Fact template update payload."""

    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=2000)
    prompt: str | None = Field(None, max_length=10000)
    schema_definition: dict | None = None
    example: dict | None = None
    is_active: bool | None = None


class FactTemplateInDB(FactTemplateBase):
    """Fact template database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_system: bool
    organization_id: int | None
    created_at: datetime
    updated_at: datetime


class FactBase(BaseModel):
    """Base fact fields."""

    fact_type: str = Field(..., max_length=50)
    title: str = Field(..., max_length=500)
    summary: str | None = Field(None, max_length=2000)
    attributes: dict | None = None
    confidence: str | None = Field(None, max_length=20)
    evidence: list[FactEvidence] | None = None
    effective_date: datetime | None = None
    competitor_id: int | None = None
    item_id: int | None = None


class FactCreate(FactBase):
    """Fact creation payload."""

    template_id: int | None = None


class FactUpdate(BaseModel):
    """Fact update payload."""

    title: str | None = Field(None, max_length=500)
    summary: str | None = Field(None, max_length=2000)
    attributes: dict | None = None
    confidence: str | None = Field(None, max_length=20)
    evidence: list[FactEvidence] | None = None
    effective_date: datetime | None = None
    verified: bool | None = None


class FactInDB(FactBase):
    """Fact database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int | None
    organization_id: int
    verified_at: datetime | None
    verified_by_user_id: int | None
    created_at: datetime
    updated_at: datetime


class FactExtractionRequest(BaseModel):
    """Request to extract facts from an intelligence item."""

    item_id: int
    fact_types: list[str] | None = None


class FactExtractionResult(BaseModel):
    """Result of fact extraction for an item."""

    item_id: int
    facts_created: int
    facts: list[FactInDB]
