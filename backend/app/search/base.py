"""Abstract base class for search engines."""

from abc import ABC, abstractmethod
from typing import Any

from app.core.logging import get_logger
from app.schemas.search import SearchResult

logger = get_logger(__name__)


class BaseSearchEngine(ABC):
    """Async search engine abstraction."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the engine with provider configuration.

        Args:
            config: Provider-specific configuration (e.g. API keys).
        """
        self.config = config or {}
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate the engine configuration.

        Raises:
            ValueError: If the configuration is invalid or missing required keys.
        """

    @abstractmethod
    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        """Execute an async search.

        Args:
            query: The search query string.
            num_results: Maximum number of results to return.

        Returns:
            A list of search results.
        """
