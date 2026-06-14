"""Google Gemini provider adapter."""

from typing import Any

from app.core.logging import get_logger
from app.providers.base import BaseProvider, ProviderResponse, ProviderUsage

logger = get_logger(__name__)


class GeminiProvider(BaseProvider):
    """Provider adapter for Google Gemini."""

    provider_type = "gemini"

    def _validate_config(self) -> None:
        """Validate that an API key is present."""
        self.api_key = self.config.get("api_key", "")
        if not self.api_key:
            raise ValueError("Gemini API key is not configured")

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
        """Execute a chat completion request against Gemini."""
        logger.warning("gemini_chat_not_implemented", model=model)
        return ProviderResponse(
            content="Gemini adapter is not fully implemented in this build.",
            usage=ProviderUsage(model=model, provider_type=self.provider_type),
        )

    async def list_models(self) -> list[dict[str, Any]]:
        """Return default Gemini models."""
        return [
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "context_window": 2097152},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "context_window": 1048576},
            {"id": "gemini-1.0-pro", "name": "Gemini 1.0 Pro", "context_window": 32768},
        ]

    async def validate_credentials(self) -> bool:
        """Validate credentials."""
        return bool(self.api_key)
