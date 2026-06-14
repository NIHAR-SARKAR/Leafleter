"""Campaign analyzer endpoints."""

from typing import Any

from fastapi import APIRouter, Depends

from app.core.deps import ActiveUserDep, DbDep, require_permissions
from app.core.logging import get_logger
from app.models.user import User
from app.services.campaign_service import campaign_service

logger = get_logger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=dict[str, str])
async def analyze_campaign(
    db: DbDep,
    campaign_name: str,
    description: str,
    metrics: str,
    provider_id: int | None = None,
    current_user: User = Depends(require_permissions("reports:write")),
) -> Any:
    """Analyze campaign results with AI."""
    result = await campaign_service.analyze(
        db,
        campaign_name=campaign_name,
        description=description,
        metrics=metrics,
        user=current_user,
        provider_id=provider_id,
    )
    return result
