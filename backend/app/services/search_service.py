"""Search and web intelligence service layer."""

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.crud.topic import topic_repository, topic_source_repository
from app.services.intelligence_hooks import on_search_executed
from app.db.base import now_utc
from app.models.topic import TopicSource
from app.schemas.search import CrawlResponse, SearchResult
from app.search.crawler import crawl_url
from app.search.registry import SearchEngineRegistry
from app.search.sitemap import parse_sitemap

logger = get_logger(__name__)


class SearchService:
    """Service for executing searches, crawling, and managing topic sources."""

    async def search(
        self,
        db: AsyncSession,
        query: str,
        engine_type: str,
        organization_id: int,
        num_results: int = 10,
    ) -> list[SearchResult]:
        """Validate provider config and execute a search.

        Args:
            db: Database session (reserved for future audit logging).
            query: Search query string.
            engine_type: Registered engine identifier (e.g. ``serpapi``).
            organization_id: Organization requesting the search.
            num_results: Maximum number of results to return.

        Returns:
            A list of search results.

        Raises:
            AppException: If the engine type is unsupported or config is missing.
        """
        if engine_type not in SearchEngineRegistry.supported():
            raise AppException(
                f"Unsupported search engine: {engine_type}",
                status_code=400,
            )

        config = self._build_engine_config(engine_type)
        engine_class = SearchEngineRegistry.get(engine_type)
        if engine_class is None:
            raise AppException(
                f"Unsupported search engine: {engine_type}",
                status_code=400,
            )

        try:
            engine = engine_class(config)
        except ValueError as exc:
            logger.warning(
                "search_provider_config_invalid",
                engine_type=engine_type,
                organization_id=organization_id,
                error=str(exc),
            )
            raise AppException(
                f"Search provider configuration invalid: {exc}",
                status_code=400,
            ) from exc

        logger.info(
            "search_request",
            engine_type=engine_type,
            organization_id=organization_id,
            query=query,
            num_results=num_results,
        )
        results = await engine.search(query, num_results)
        try:
            on_search_executed(query, results, organization_id=organization_id)
        except Exception as exc:
            logger.warning("intelligence_search_hook_failed", error=str(exc))
        return results

    async def crawl(self, url: str) -> CrawlResponse:
        """Crawl a URL and return extracted content."""
        result = await crawl_url(url)
        return CrawlResponse(**result)

    async def parse_sitemap(self, url: str) -> list[str]:
        """Parse a sitemap and return discovered URLs."""
        return await parse_sitemap(url)

    async def add_search_source(
        self,
        db: AsyncSession,
        *,
        topic_id: int,
        query: str,
        engine_type: str,
        organization_id: int,
        created_by_id: int | None = None,
    ) -> TopicSource:
        """Create a topic source and fetch its initial search results.

        Args:
            db: Database session.
            topic_id: ID of the topic to attach the source to.
            query: Search query to store and execute.
            engine_type: Registered search engine identifier.
            organization_id: Organization that owns the topic.
            created_by_id: Optional ID of the user creating the source.

        Returns:
            The created ``TopicSource`` with fetch status populated.
        """
        topic = await topic_repository.get_or_404_for_organization(
            db, topic_id, organization_id
        )

        source_data: dict[str, Any] = {
            "topic_id": topic.id,
            "source_type": "search",
            "name": f"Search: {query[:200]}",
            "url": None,
            "query": query,
            "platform": engine_type,
            "account_id": None,
            "configuration": {"engine_type": engine_type, "num_results": 10},
            "fetch_status": "pending",
            "fetch_error": None,
            "raw_data": None,
        }
        if created_by_id is not None:
            source_data["created_by_id"] = created_by_id

        source = await topic_source_repository.create(db, obj_in=source_data)

        try:
            results = await self.search(
                db,
                query=query,
                engine_type=engine_type,
                organization_id=organization_id,
                num_results=10,
            )
            source.last_fetched_at = now_utc()
            source.fetch_status = "success"
            source.raw_data = json.dumps(
                [result.model_dump() for result in results],
                default=str,
            )
            logger.info(
                "search_source_fetched",
                source_id=source.id,
                topic_id=topic_id,
                engine_type=engine_type,
                results=len(results),
            )
        except Exception as exc:
            source.fetch_status = "error"
            source.fetch_error = str(exc)
            logger.exception(
                "search_source_fetch_failed",
                source_id=source.id,
                topic_id=topic_id,
                engine_type=engine_type,
                error=str(exc),
            )

        await db.commit()
        await db.refresh(source)
        return source

    def _build_engine_config(self, engine_type: str) -> dict[str, Any]:
        """Build a configuration dictionary for a search engine from env vars."""
        if engine_type == "serpapi":
            return {"api_key": settings.SERPAPI_API_KEY}
        if engine_type == "bing":
            return {"api_key": settings.BING_API_KEY}
        if engine_type == "tavily":
            return {"api_key": settings.TAVILY_API_KEY}
        if engine_type == "google_cse":
            return {
                "api_key": settings.GOOGLE_CSE_KEY,
                "cx": settings.GOOGLE_CSE_CX,
            }
        if engine_type == "duckduckgo":
            return {
                "api_key": "",
            }
        raise AppException(
            f"Unsupported search engine: {engine_type}",
            status_code=400,
        )


search_service = SearchService()
