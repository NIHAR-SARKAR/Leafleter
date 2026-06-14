"""Abstract base provider for AI services."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProviderUsage:
    """Standardized token/cost usage for an AI request."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    model: str = ""
    provider_type: str = ""


@dataclass
class ProviderResponse:
    """Standardized response from any AI provider."""

    content: str = ""
    raw_response: dict[str, Any] = field(default_factory=dict)
    usage: ProviderUsage = field(default_factory=ProviderUsage)
    finish_reason: str | None = None


class BaseProvider(ABC):
    """Abstract adapter for AI providers."""

    provider_type: str = ""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the provider with configuration.

        Args:
            config: Provider-specific settings such as API keys and base URLs.
        """
        self.config = config
        self._validate_config()
        self._client: Any | None = None

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider configuration."""

    @abstractmethod
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
        """Execute a chat completion request."""

    @abstractmethod
    async def list_models(self) -> list[dict[str, Any]]:
        """Return supported models for the provider."""

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate that configured credentials work."""

    async def embeddings(
        self,
        *,
        texts: list[str],
        model: str,
        **kwargs: Any,
    ) -> list[list[float]]:
        """Generate embeddings (optional; providers may override)."""
        raise NotImplementedError("Embeddings not supported by this provider")

    def _estimate_cost(
        self,
        *,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate request cost from config pricing.

        Override in subclasses for provider-specific pricing.
        """
        pricing = self.config.get("pricing", {})
        model_pricing = pricing.get(model, {})
        input_price = model_pricing.get("input", 0.0)
        output_price = model_pricing.get("output", 0.0)
        cost = (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)
        return round(cost, 6)
