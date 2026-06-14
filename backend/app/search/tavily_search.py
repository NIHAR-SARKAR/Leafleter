"""Tavily search engine stub."""

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.search import SearchResult
from app.search.base import BaseSearchEngine

logger = get_logger(__name__)


class TavilySearchEngine(BaseSearchEngine):
    """Stub implementation for the Tavily Search API."""

    def _validate_config(self) -> None:
        """Ensure the Tavily API key is configured."""
        api_key = self.config.get("api_key") or settings.TAVILY_API_KEY
        if not api_key:
            raise ValueError("Tavily API key is not configured")

    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        """Return an empty result set while the provider config is validated."""
        logger.info(
            "tavily_search_stub",
            query=query,
            num_results=num_results,
            message="Tavily search is not implemented; returning empty results",
        )
        return []
