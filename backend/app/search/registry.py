"""Search engine registry mapping engine types to implementations."""

from typing import TYPE_CHECKING

from app.core.logging import get_logger
from app.search.bing_search import BingSearchEngine
from app.search.duckduckgo_search import DuckDuckGoSearchEngine
from app.search.google_cse import GoogleCSESearchEngine
from app.search.serpapi_search import SerpapiSearchEngine
from app.search.tavily_search import TavilySearchEngine

if TYPE_CHECKING:
    from app.search.base import BaseSearchEngine

logger = get_logger(__name__)


class SearchEngineRegistry:
    """Registry of supported search engine implementations."""

    _engines: dict[str, type["BaseSearchEngine"]] = {
        "serpapi": SerpapiSearchEngine,
        "bing": BingSearchEngine,
        "tavily": TavilySearchEngine,
        "google_cse": GoogleCSESearchEngine,
        "duckduckgo": DuckDuckGoSearchEngine,
    }

    @classmethod
    def get(cls, engine_type: str) -> type["BaseSearchEngine"] | None:
        """Return the engine class for a given type, or None if unsupported."""
        return cls._engines.get(engine_type)

    @classmethod
    def supported(cls) -> list[str]:
        """Return a list of supported engine type identifiers."""
        return list(cls._engines.keys())

    @classmethod
    def register(cls, engine_type: str, engine_class: type["BaseSearchEngine"]) -> None:
        """Register a new engine implementation."""
        cls._engines[engine_type] = engine_class
        logger.info("search_engine_registered", engine_type=engine_type)
