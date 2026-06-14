"""Provider-specific configuration schemas.

These schemas document and validate the optional ``config`` dict stored on a
``Provider`` record. They are used by the API schemas to give early feedback
when a provider is created or updated.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OpenAIConfig(BaseModel):
    """Optional configuration for the OpenAI provider."""

    model_config = ConfigDict(extra="forbid")

    organization: str | None = Field(None, max_length=100)
    project: str | None = Field(None, max_length=100)


class AzureOpenAIConfig(BaseModel):
    """Optional configuration for the Azure OpenAI / Azure AI Foundry provider."""

    model_config = ConfigDict(extra="forbid")

    deployment: str | None = Field(
        None,
        max_length=100,
        description="Deployment or model name used in the request path/body.",
    )
    api_pattern: Literal[
        "azure_openai_legacy",
        "azure_openai_v1",
        "azure_responses",
        "azure_ai_foundry",
    ] | None = Field(
        None,
        description="Explicit API pattern override. Auto-detected when omitted.",
    )
    use_responses_api: bool | None = Field(
        None,
        description="Prefer the Responses API when the model supports it.",
    )
    model_name: str | None = Field(
        None,
        max_length=100,
        description="Model name passed in the request body.",
    )
    responses_api_version: str | None = Field(
        None,
        max_length=50,
        description="api-version for the Responses API endpoint.",
    )
    v1_api_version: str | None = Field(
        None,
        max_length=50,
        description="api-version query parameter for the v1 chat endpoint.",
    )
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(
        None,
        description="Reasoning effort for supported reasoning models.",
    )
    verbosity: Literal["low", "medium", "high"] | None = Field(
        None,
        description="Output verbosity for supported models.",
    )


_PROVIDER_CONFIG_SCHEMAS: dict[str, type[BaseModel]] = {
    "openai": OpenAIConfig,
    "azure_openai": AzureOpenAIConfig,
}


def validate_provider_config(provider_type: str, config: dict | None) -> dict:
    """Validate and normalize a provider config dict.

    Unknown provider types are returned unchanged so the registry can enforce
    its own validation at runtime.
    """
    config = config or {}
    schema_cls = _PROVIDER_CONFIG_SCHEMAS.get(provider_type)
    if schema_cls is None:
        return config
    return schema_cls.model_validate(config).model_dump(exclude_unset=True)
