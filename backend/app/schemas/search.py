"""Pydantic schemas for the Search Framework and Web Intelligence module."""

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SearchResult(BaseModel):
    """A single search result returned by an engine."""

    model_config = ConfigDict(populate_by_name=True)

    title: str
    url: str
    snippet: str = ""
    source: str | None = None
    position: int | None = None


class SearchRequest(BaseModel):
    """Payload for running a web search."""

    query: str = Field(..., min_length=1, max_length=1000)
    engine_type: str = Field(..., min_length=1, max_length=50)
    num_results: int = Field(default=10, ge=1, le=100)


class SearchResponse(BaseModel):
    """Response payload for a web search."""

    query: str
    engine_type: str
    results: list[SearchResult]
    total_results: int


class CrawlRequest(BaseModel):
    """Payload for crawling a single URL."""

    url: HttpUrl


class CrawlResponse(BaseModel):
    """Response payload for a crawled URL."""

    url: str
    title: str
    text: str
    links: list[str]


class SitemapRequest(BaseModel):
    """Payload for parsing a sitemap."""

    url: HttpUrl
