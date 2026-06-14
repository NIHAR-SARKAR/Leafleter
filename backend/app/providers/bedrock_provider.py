"""AWS Bedrock provider adapter."""

from typing import Any

from app.core.logging import get_logger
from app.providers.base import BaseProvider, ProviderResponse, ProviderUsage

logger = get_logger(__name__)


class BedrockProvider(BaseProvider):
    """Provider adapter for AWS Bedrock."""

    provider_type = "bedrock"

    def _validate_config(self) -> None:
        """Validate AWS credentials."""
        self.access_key = self.config.get("access_key", "")
        self.secret_key = self.config.get("secret_key", "")
        self.region = self.config.get("region", "us-east-1")
        if not self.access_key or not self.secret_key:
            raise ValueError("AWS access key and secret key are required")

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
        """Execute a chat completion request against Bedrock."""
        logger.warning("bedrock_chat_not_implemented", model=model)
        return ProviderResponse(
            content="Bedrock adapter is not fully implemented in this build.",
            usage=ProviderUsage(model=model, provider_type=self.provider_type),
        )

    async def list_models(self) -> list[dict[str, Any]]:
        """Return default Bedrock models."""
        return [
            {"id": "anthropic.claude-3-5-sonnet-20241022-v2:0", "name": "Claude 3.5 Sonnet", "context_window": 200000},
            {"id": "amazon.titan-text-premier-v1:0", "name": "Titan Text Premier", "context_window": 32768},
        ]

    async def validate_credentials(self) -> bool:
        """Validate credentials."""
        return bool(self.access_key and self.secret_key)
