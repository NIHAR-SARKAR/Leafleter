"""Provider registry for AI adapter discovery."""

from typing import TYPE_CHECKING, Any

from app.core.logging import get_logger
from app.providers.openai_provider import OpenAIProvider

if TYPE_CHECKING:
    from app.providers.base import BaseProvider

logger = get_logger(__name__)


class ProviderRegistry:
    """Registry mapping provider_type strings to provider adapter classes."""

    _providers: dict[str, type["BaseProvider"]] = {
        "openai": OpenAIProvider,
        # Additional providers registered lazily to avoid heavy imports at startup.
    }

    @classmethod
    def register(
        cls,
        provider_type: str,
        provider_class: type["BaseProvider"],
    ) -> None:
        """Register a provider adapter."""
        cls._providers[provider_type] = provider_class
        logger.info("provider_registered", provider_type=provider_type)

    @classmethod
    def get(cls, provider_type: str) -> type["BaseProvider"] | None:
        """Return the provider class for a type, or None."""
        provider_type = provider_type.lower().strip()
        return cls._providers.get(provider_type)

    @classmethod
    def supported(cls) -> list[str]:
        """Return supported provider type identifiers."""
        return sorted(cls._providers.keys())

    @classmethod
    def create(cls, provider_type: str, config: dict[str, Any]) -> "BaseProvider":
        """Instantiate a provider adapter."""
        provider_class = cls.get(provider_type)
        if provider_class is None:
            raise ValueError(f"Unsupported provider type: {provider_type}")
        return provider_class(config)


# Register additional provider adapters.
def _register_providers() -> None:
    """Lazily register provider adapters to avoid import cycles."""
    from app.providers.azure_openai_provider import AzureOpenAIProvider
    from app.providers.bedrock_provider import BedrockProvider
    from app.providers.claude_provider import ClaudeProvider
    from app.providers.gemini_provider import GeminiProvider
    from app.providers.kimi_provider import KimiProvider
    from app.providers.openrouter_provider import OpenRouterProvider
    from app.providers.qwen_provider import QwenProvider

    registry = {
        "azure_openai": AzureOpenAIProvider,
        # "anthropic": ClaudeProvider,
        # "claude": ClaudeProvider,
        # "gemini": GeminiProvider,
        # "openrouter": OpenRouterProvider,
        # "bedrock": BedrockProvider,
        "kimi": KimiProvider,
        # "qwen": QwenProvider,
    }
    for provider_type, provider_class in registry.items():
        ProviderRegistry.register(provider_type, provider_class)


_register_providers()
