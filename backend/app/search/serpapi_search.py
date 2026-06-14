"""SerpApi search engine implementation."""

from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.schemas.search import SearchResult
from app.search.base import BaseSearchEngine

logger = get_logger(__name__)

SERPAPI_BASE_URL = "https://serpapi.com/search"


class SerpapiSearchEngine(BaseSearchEngine):
    """Search engine implementation backed by SerpApi (Google results)."""

    def _validate_config(self) -> None:
        """Ensure an API key is configured."""
        self.api_key = self.config.get("api_key") or settings.SERPAPI_API_KEY
        if not self.api_key:
            raise ValueError("SerpApi API key is not configured")

    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        """Fetch organic search results from SerpApi."""
        params: dict[str, Any] = {
            "engine": "google",
            "q": query,
            "num": min(num_results, 100),
            "api_key": self.api_key,
            "source": "python",
        }

        logger.info("serpapi_search_request", query=query, num_results=num_results)

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                response = await client.get(SERPAPI_BASE_URL, params=params)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "serpapi_http_error",
                    status_code=exc.response.status_code,
                    body=exc.response.text,
                )
                raise AppException(
                    "Search engine returned an error",
                    status_code=exc.response.status_code,
                ) from exc
            except httpx.RequestError as exc:
                logger.error("serpapi_request_error", error=str(exc))
                raise AppException("Failed to reach search engine") from exc

        data = response.json()
        organic_results = data.get("organic_results", [])

        results: list[SearchResult] = []
        for idx, item in enumerate(organic_results[:num_results], start=1):
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            if not link:
                continue
            results.append(
                SearchResult(
                    title=title or "Untitled",
                    url=link,
                    snippet=snippet,
                    source="serpapi",
                    position=idx,
                )
            )

        logger.info(
            "serpapi_search_complete",
            query=query,
            returned=len(results),
        )
        return results
