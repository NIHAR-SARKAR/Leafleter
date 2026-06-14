"""OpenRouter provider adapter."""

from typing import Any

from app.core.logging import get_logger
from app.providers.base import BaseProvider, ProviderResponse, ProviderUsage

logger = get_logger(__name__)


class OpenRouterProvider(BaseProvider):
    """Provider adapter for OpenRouter."""

    provider_type = "openrouter"

    def _validate_config(self) -> None:
        """Validate that an API key is present."""
        self.api_key = self.config.get("api_key", "")
        if not self.api_key:
            raise ValueError("OpenRouter API key is not configured")

    async def chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        response_format: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Execute a chat completion request against OpenRouter."""
        logger.warning("openrouter_chat_not_implemented", model=model)
        return ProviderResponse(
            content="OpenRouter adapter is not fully implemented in this build.",
            usage=ProviderUsage(model=model, provider_type=self.provider_type),
        )

    async def list_models(self) -> list[dict[str, Any]]:
        """Return default OpenRouter models."""
        return [
            {"id": "openai/gpt-4o", "name": "OpenAI GPT-4o", "context_window": 128000},
            {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "context_window": 200000},
        ]

    async def validate_credentials(self) -> bool:
        """Validate credentials."""
        return bool(self.api_key)
