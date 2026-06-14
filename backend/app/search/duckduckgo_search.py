"""DuckDuckGo search engine (no API key required)."""

import asyncio

from ddgs import DDGS
from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException

from app.core.logging import get_logger
from app.schemas.search import SearchResult
from app.search.base import BaseSearchEngine

logger = get_logger(__name__)


class DuckDuckGoSearchEngine(BaseSearchEngine):
    """Search engine backed by DuckDuckGo via the `ddgs` package.

    No API key or credentials are required.  Optional config keys:

    - ``region``      – DuckDuckGo region code, e.g. ``"us-en"`` (default: ``None``).
    - ``safesearch``  – ``"on"``, ``"moderate"``, or ``"off"`` (default: ``"moderate"``).
    - ``timelimit``   – ``"d"`` / ``"w"`` / ``"m"`` / ``"y"`` or ``None`` (default: ``None``).
    - ``backend``     – ``"auto"``, ``"html"``, or ``"lite"`` (default: ``"auto"``).
    """

    def _validate_config(self) -> None:
        """No credentials are needed; validate optional knobs only."""
        safesearch = self.config.get("safesearch", "moderate")
        if safesearch not in {"on", "moderate", "off"}:
            raise ValueError(
                f"Invalid safesearch value '{safesearch}'. "
                "Must be one of: 'on', 'moderate', 'off'."
            )

        backend = self.config.get("backend", "auto")
        if backend not in {"auto", "html", "lite"}:
            raise ValueError(
                f"Invalid backend value '{backend}'. "
                "Must be one of: 'auto', 'html', 'lite'."
            )

    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        """Return up to *num_results* web results for *query* from DuckDuckGo.

        The underlying ``ddgs`` client is synchronous, so the blocking call is
        offloaded to a thread pool via :func:`asyncio.to_thread` to keep the
        event loop free.
        """
        logger.info(
            "duckduckgo_search",
            query=query,
            num_results=num_results,
        )

        region: str | None = self.config.get("region")
        safesearch: str = self.config.get("safesearch", "moderate")
        timelimit: str | None = self.config.get("timelimit")
        backend: str = self.config.get("backend", "auto")

        try:
            raw: list[dict] = await asyncio.to_thread(
                self._sync_search,
                query=query,
                num_results=num_results,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                backend=backend,
            )
        except RatelimitException:
            logger.warning(
                "duckduckgo_ratelimit",
                query=query,
                message="DuckDuckGo rate-limited this request; returning empty results",
            )
            return []
        except TimeoutException:
            logger.warning(
                "duckduckgo_timeout",
                query=query,
                message="DuckDuckGo request timed out; returning empty results",
            )
            return []
        except DDGSException as exc:
            logger.error(
                "duckduckgo_error",
                query=query,
                error=str(exc),
            )
            return []

        return [
            SearchResult(
                title=item.get("title", ""),
                url=item.get("href", ""),
                snippet=item.get("body", ""),
            )
            for item in raw
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sync_search(
        query: str,
        num_results: int,
        region: str | None,
        safesearch: str,
        timelimit: str | None,
        backend: str,
    ) -> list[dict]:
        """Blocking DuckDuckGo text search – runs in a thread pool."""
        with DDGS() as ddgs:
            return ddgs.text(
                query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                backend=backend,
                max_results=num_results,
            )