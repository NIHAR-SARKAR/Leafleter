"""Shared stub adapter behavior for providers implemented later."""

from typing import Any

from app.core.logging import get_logger
from app.providers.base import BaseProvider, ProviderResponse, ProviderUsage

logger = get_logger(__name__)


class StubProvider(BaseProvider):
    """Base class for provider adapters that are not yet fully integrated.

    Validates credentials syntactically and returns a realistic model list.
    Chat and embedding calls raise NotImplementedError by default.
    """

    provider_type = "stub"
    default_api_base: str = ""
    models: list[dict[str, Any]] = []

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if self.api_base is None and self.default_api_base:
            self.api_base = self.default_api_base

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Stub: return a placeholder response for development."""
        logger.warning(
            "stub_chat_completion",
            provider=self.provider_type,
            model=model,
        )
        return ProviderResponse(
            content=f"[{self.provider_type}] Stub response for {model}.",
            model=model,
            usage=ProviderUsage(),
            finish_reason="stop",
        )

    async def embeddings(self, texts: list[str], model: str, **kwargs: Any) -> list[list[float]]:
        """Stub: return zero embeddings."""
        logger.warning("stub_embeddings", provider=self.provider_type, model=model)
        return [[0.0] * 1536 for _ in texts]

    async def list_models(self) -> list[dict[str, Any]]:
        """Return the static model catalog for this provider."""
        return list(self.models)

    async def validate_credentials(self) -> tuple[bool, str]:
        """Validate that an API key or required config is present."""
        if self.api_key is None and self.provider_type not in {"bedrock", "azure_openai"}:
            return False, "API key is missing"
        if self.provider_type == "bedrock":
            if not self.config.get("aws_access_key_id") or not self.config.get("aws_secret_access_key"):
                return False, "AWS credentials are missing"
        if self.provider_type == "azure_openai":
            if not self.api_base:
                return False, "Azure endpoint (api_base) is required"
            if not self.api_key:
                return False, "Azure API key is required"
        return True, f"{self.provider_type} credentials appear valid (stub)"
