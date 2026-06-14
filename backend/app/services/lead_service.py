"""Lead discovery service."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger

logger = get_logger(__name__)


class LeadService:
    """Service for discovering leads from public sources."""

    async def discover(
        self,
        db: AsyncSession,
        *,
        query: str,
        industry: str | None = None,
        location: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Discover leads based on search criteria.

        This MVP implementation returns structured placeholder data.
        In production, this would integrate with business data APIs.
        """
        logger.info("lead_discovery", query=query, industry=industry, location=location)
        return [
            {
                "name": f"{query.title()} Prospects Inc.",
                "industry": industry or "Technology",
                "location": location or "United States",
                "website": f"https://{query.replace(' ', '').lower()}-prospects.example.com",
                "confidence": 0.85,
            }
            for _ in range(min(limit, 20))
        ]


lead_service = LeadService()
