"""Tests for the Azure OpenAI provider adapter."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers.azure_openai_provider import AzureAPIPattern, AzureOpenAIProvider


@pytest.fixture
def base_config():
    """Return a valid Azure provider configuration."""
    return {
        "api_key": "test-api-key",
        "api_base": "https://test.openai.azure.com",
        "api_version": "2024-12-01-preview",
    }


@pytest.fixture
def provider(base_config):
    """Return an initialized Azure provider."""
    return AzureOpenAIProvider(base_config)


@pytest.mark.asyncio
async def test_chat_completion_legacy_url(provider):
    """Legacy pattern uses deployment-specific URL with api-version."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {"content": "Hello"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch.object(provider, "_client", mock_client):
        response = await provider.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            model="gpt-4",
            temperature=0.5,
            max_tokens=100,
        )

    assert response.content == "Hello"
    assert response.finish_reason == "stop"
    assert response.usage.input_tokens == 5
    assert response.usage.output_tokens == 2
    assert response.usage.total_tokens == 7

    called_url = mock_client.post.call_args[0][0]
    assert "deployments/gpt-4/chat/completions" in called_url
    assert "api-version=2024-12-01-preview" in called_url


@pytest.mark.asyncio
async def test_chat_completion_v1_url_and_body(provider):
    """V1 pattern routes to /openai/v1/chat/completions with model in body."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch.object(provider, "_client", mock_client):
        await provider.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            model="gpt-4o",
        )

    called_url = mock_client.post.call_args[0][0]
    assert called_url == "https://test.openai.azure.com/openai/v1/chat/completions"

    payload = mock_client.post.call_args.kwargs["json"]
    assert payload["model"] == "gpt-4o"
    assert payload["messages"][0]["role"] == "user"


@pytest.mark.asyncio
async def test_chat_completion_responses_api(provider):
    """Responses API uses /openai/v1/responses and 'input' array."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "output_text": "Response text",
        "usage": {"input_tokens": 3, "output_tokens": 4, "total_tokens": 7},
        "status": "completed",
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch.object(provider, "_client", mock_client):
        response = await provider.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            model="gpt-5.3-codex",
        )

    assert response.content == "Response text"
    assert response.finish_reason == "completed"

    called_url = mock_client.post.call_args[0][0]
    assert "responses" in called_url

    payload = mock_client.post.call_args.kwargs["json"]
    assert "input" in payload
    assert "messages" not in payload
    assert "temperature" not in payload
    assert "max_tokens" not in payload


@pytest.mark.asyncio
async def test_chat_completion_foundry_url(provider):
    """AI Foundry model routes to /chat/completions with model in body."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Foundry"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch.object(provider, "_client", mock_client):
        await provider.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            model="deepseek-r1",
        )

    called_url = mock_client.post.call_args[0][0]
    assert called_url.endswith("/chat/completions")

    payload = mock_client.post.call_args.kwargs["json"]
    assert payload["model"] == "deepseek-r1"


@pytest.mark.asyncio
async def test_reasoning_model_uses_max_completion_tokens(provider):
    """Reasoning models use max_completion_tokens instead of max_tokens."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "R"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch.object(provider, "_client", mock_client):
        await provider.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            model="o3-mini",
            max_tokens=500,
        )

    payload = mock_client.post.call_args.kwargs["json"]
    assert payload["max_completion_tokens"] == 500
    assert "max_tokens" not in payload


@pytest.mark.asyncio
async def test_developer_role_for_gpt5(provider):
    """GPT-5 family prefers developer role for system messages."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch.object(provider, "_client", mock_client):
        await provider.chat_completion(
            messages=[
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hi"},
            ],
            model="gpt-5",
        )

    payload = mock_client.post.call_args.kwargs["json"]
    assert payload["messages"][0]["role"] == "developer"


def test_detect_model_config_forced_pattern(base_config):
    """api_pattern config overrides auto-detection."""
    base_config["api_pattern"] = "azure_ai_foundry"
    p = AzureOpenAIProvider(base_config)
    config = p._detect_model_config("gpt-4")
    assert p._resolve_pattern(config) == AzureAPIPattern.AZURE_AI_FOUNDRY


def test_detect_unknown_model_defaults_to_legacy(provider):
    """Unknown model names fall back to the legacy pattern."""
    config = provider._detect_model_config("some-custom-model")
    assert config["default"] == AzureAPIPattern.AZURE_OPENAI_LEGACY


@pytest.mark.asyncio
async def test_list_models_returns_defaults(provider):
    """list_models returns a curated default catalog."""
    models = await provider.list_models()
    ids = {m["id"] for m in models}
    assert "gpt-4.1" in ids
    assert "gpt-4o" in ids
    assert "o3-mini" in ids
    assert "deepseek-r1" in ids


@pytest.mark.asyncio
async def test_validate_credentials_success(provider):
    """validate_credentials returns True on successful minimal request."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": ""}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch.object(provider, "_client", mock_client):
        assert await provider.validate_credentials() is True


@pytest.mark.asyncio
async def test_validate_credentials_failure(base_config):
    """validate_credentials returns False when the request fails."""
    p = AzureOpenAIProvider(base_config)
    mock_client = AsyncMock()
    mock_client.post.side_effect = Exception("connection refused")

    with patch.object(p, "_client", mock_client):
        assert await p.validate_credentials() is False


def test_missing_config_raises():
    """Missing api_key or api_base raises ValueError."""
    with pytest.raises(ValueError, match="Azure OpenAI API key and endpoint"):
        AzureOpenAIProvider({})
