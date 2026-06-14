"""Google Custom Search Engine stub."""

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.search import SearchResult
from app.search.base import BaseSearchEngine

logger = get_logger(__name__)


class GoogleCSESearchEngine(BaseSearchEngine):
    """Stub implementation for Google Custom Search Engine (CSE)."""

    def _validate_config(self) -> None:
        """Ensure the Google CSE key and search engine ID are configured."""
        api_key = self.config.get("api_key") or settings.GOOGLE_CSE_KEY
        cx = self.config.get("cx") or settings.GOOGLE_CSE_CX
        if not api_key:
            raise ValueError("Google CSE API key is not configured")
        if not cx:
            raise ValueError("Google CSE search engine ID (cx) is not configured")

    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        """Return an empty result set while the provider config is validated."""
        logger.info(
            "google_cse_search_stub",
            query=query,
            num_results=num_results,
            message="Google CSE search is not implemented; returning empty results",
        )
        return []
