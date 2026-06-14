"""Tests for provider Pydantic schemas and config validation."""

import pytest

from app.schemas.provider import ProviderCreate, ProviderUpdate


def test_provider_create_accepts_azure_config():
    """Azure-specific config fields are validated and normalized."""
    provider = ProviderCreate(
        name="Azure",
        provider_type="azure_openai",
        api_base="https://test.openai.azure.com",
        api_version="2024-12-01-preview",
        config={
            "deployment": "gpt-4o",
            "api_pattern": "azure_openai_v1",
            "reasoning_effort": "medium",
        },
    )
    assert provider.config["deployment"] == "gpt-4o"
    assert provider.config["api_pattern"] == "azure_openai_v1"
    assert provider.config["reasoning_effort"] == "medium"


def test_provider_create_rejects_invalid_azure_pattern():
    """Invalid api_pattern values are rejected."""
    with pytest.raises(ValueError):
        ProviderCreate(
            name="Azure",
            provider_type="azure_openai",
            config={"api_pattern": "invalid_pattern"},
        )


def test_provider_create_rejects_unknown_azure_field():
    """Unknown config fields are rejected for known providers."""
    with pytest.raises(ValueError):
        ProviderCreate(
            name="Azure",
            provider_type="azure_openai",
            config={"unknown_field": "value"},
        )


def test_provider_update_validates_config_when_type_present():
    """Config is validated when provider_type is supplied on update."""
    provider = ProviderUpdate(
        provider_type="azure_openai",
        config={"deployment": "gpt-4.1"},
    )
    assert provider.config["deployment"] == "gpt-4.1"


def test_provider_update_skips_validation_without_type():
    """Config is left untouched when provider_type is omitted on update."""
    provider = ProviderUpdate(config={"custom_key": "value"})
    assert provider.config["custom_key"] == "value"
