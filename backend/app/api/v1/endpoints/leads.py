"""Lead discovery endpoints."""

from typing import Any

from fastapi import APIRouter

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep
from app.core.logging import get_logger
from app.services.lead_service import lead_service

logger = get_logger(__name__)
router = APIRouter()


@router.post("/discover", response_model=list[dict[str, Any]])
async def discover_leads(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    query: str,
    industry: str | None = None,
    location: str | None = None,
    limit: int = 10,
) -> Any:
    """Discover leads from public sources."""
    leads = await lead_service.discover(
        db, query=query, industry=industry, location=location, limit=limit
    )
    return leads
