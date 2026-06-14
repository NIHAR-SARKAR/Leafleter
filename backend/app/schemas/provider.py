"""Provider Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.providers.config_schemas import validate_provider_config


class ProviderModelBase(BaseModel):
    """Base provider model fields."""

    external_id: str = Field(..., max_length=100)
    name: str = Field(..., max_length=100)
    is_active: bool = True
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0
    context_window: int | None = None
    max_tokens: int | None = None
    supports_vision: bool = False
    supports_json: bool = False


class ProviderModelCreate(ProviderModelBase):
    """Provider model creation payload."""

    pass


class ProviderModelUpdate(BaseModel):
    """Provider model update payload."""

    name: str | None = Field(None, max_length=100)
    is_active: bool | None = None
    input_cost_per_1k: float | None = None
    output_cost_per_1k: float | None = None
    context_window: int | None = None
    max_tokens: int | None = None
    supports_vision: bool | None = None
    supports_json: bool | None = None


class ProviderModelInDB(ProviderModelBase):
    """Provider model database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_id: int
    created_at: datetime
    updated_at: datetime


class ProviderBase(BaseModel):
    """Base provider fields."""

    name: str = Field(..., max_length=100)
    provider_type: str = Field(..., max_length=50)
    is_active: bool = True
    is_default: bool = False
    api_base: str | None = Field(None, max_length=500)
    api_version: str | None = Field(None, max_length=50)
    region: str | None = Field(None, max_length=50)
    rate_limit_rpm: int | None = None
    rate_limit_tpm: int | None = None
    fallback_order: int = 0
    config: dict | None = None


class ProviderCreate(ProviderBase):
    """Provider creation payload."""

    api_key: str | None = Field(None, max_length=1000)
    models: list[ProviderModelCreate] = []

    @model_validator(mode="after")
    def validate_config(self) -> "ProviderCreate":
        """Validate provider-type-specific config."""
        if self.config is not None:
            self.config = validate_provider_config(self.provider_type, self.config)
        return self


class ProviderUpdate(BaseModel):
    """Provider update payload."""

    name: str | None = Field(None, max_length=100)
    provider_type: str | None = Field(None, max_length=50)
    is_active: bool | None = None
    is_default: bool | None = None
    api_base: str | None = Field(None, max_length=500)
    api_version: str | None = Field(None, max_length=50)
    region: str | None = Field(None, max_length=50)
    rate_limit_rpm: int | None = None
    rate_limit_tpm: int | None = None
    fallback_order: int | None = None
    config: dict | None = None
    api_key: str | None = Field(None, max_length=1000)

    @model_validator(mode="after")
    def validate_config(self) -> "ProviderUpdate":
        """Validate provider-type-specific config."""
        if self.config is not None and self.provider_type is not None:
            self.config = validate_provider_config(self.provider_type, self.config)
        return self


class ProviderInDB(ProviderBase):
    """Provider database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime


class ProviderPublic(ProviderInDB):
    """Public provider response with models."""

    models: list[ProviderModelInDB]


class ProviderShort(BaseModel):
    """Compact provider reference."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    provider_type: str


class ProviderTestRequest(BaseModel):
    """Request to test a provider connection."""

    api_key: str | None = Field(None, max_length=1000)


class ProviderTestResponse(BaseModel):
    """Response from a provider connection test."""

    success: bool
    message: str
    models: list[dict] = []


class ProviderChatRequest(BaseModel):
    """Request to chat directly through a provider."""

    model: str = Field(..., max_length=100)
    messages: list[dict[str, str]]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1)
    session_id: str | None = Field(default=None, max_length=255)
