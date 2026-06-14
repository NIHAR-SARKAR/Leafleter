"""Moonshot Kimi provider adapter."""

from typing import Any

from app.core.logging import get_logger
from app.providers.base import BaseProvider, ProviderResponse, ProviderUsage

logger = get_logger(__name__)


class KimiProvider(BaseProvider):
    """Provider adapter for Moonshot Kimi."""

    provider_type = "kimi"

    def _validate_config(self) -> None:
        """Validate that an API key is present."""
        self.api_key = self.config.get("api_key", "")
        if not self.api_key:
            raise ValueError("Kimi API key is not configured")

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
        """Execute a chat completion request against Kimi."""
        logger.warning("kimi_chat_not_implemented", model=model)
        return ProviderResponse(
            content="Kimi adapter is not fully implemented in this build.",
            usage=ProviderUsage(model=model, provider_type=self.provider_type),
        )

    async def list_models(self) -> list[dict[str, Any]]:
        """Return default Kimi models."""
        return [
            {"id": "moonshot-v1-8k", "name": "Kimi 8K", "context_window": 8192},
            {"id": "moonshot-v1-32k", "name": "Kimi 32K", "context_window": 32768},
            {"id": "moonshot-v1-128k", "name": "Kimi 128K", "context_window": 128000},
        ]

    async def validate_credentials(self) -> bool:
        """Validate credentials."""
        return bool(self.api_key)
