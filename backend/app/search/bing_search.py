"""Bing Web Search API engine stub."""

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.search import SearchResult
from app.search.base import BaseSearchEngine

logger = get_logger(__name__)


class BingSearchEngine(BaseSearchEngine):
    """Stub implementation for the Bing Web Search API."""

    def _validate_config(self) -> None:
        """Ensure the Bing API key is configured."""
        api_key = self.config.get("api_key") or settings.BING_API_KEY
        if not api_key:
            raise ValueError("Bing API key is not configured")

    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        """Return an empty result set while the provider config is validated."""
        logger.info(
            "bing_search_stub",
            query=query,
            num_results=num_results,
            message="Bing search is not implemented; returning empty results",
        )
        return []
