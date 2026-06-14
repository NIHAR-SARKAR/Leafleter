"""Search Framework and Web Intelligence endpoints."""

from typing import Any

from fastapi import APIRouter

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep
from app.core.logging import get_logger
from app.schemas.search import (
    CrawlRequest,
    CrawlResponse,
    SearchRequest,
    SearchResponse,
    SitemapRequest,
)
from app.services.search_service import search_service

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=SearchResponse)
async def search(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    obj_in: SearchRequest,
) -> Any:
    """Execute a web search using the configured provider."""
    results = await search_service.search(
        db,
        query=obj_in.query,
        engine_type=obj_in.engine_type,
        organization_id=org_id,
        num_results=obj_in.num_results,
    )
    return SearchResponse(
        query=obj_in.query,
        engine_type=obj_in.engine_type,
        results=results,
        total_results=len(results),
    )


@router.post("/crawl", response_model=CrawlResponse)
async def crawl(
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    obj_in: CrawlRequest,
) -> Any:
    """Crawl a single URL and extract structured content."""
    return await search_service.crawl(str(obj_in.url))


@router.post("/sitemap", response_model=list[str])
async def parse_sitemap(
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    obj_in: SitemapRequest,
) -> Any:
    """Parse a sitemap XML file and return discovered URLs."""
    return await search_service.parse_sitemap(str(obj_in.url))
