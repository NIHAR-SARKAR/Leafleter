"""AI debate engine endpoints."""

from typing import Any

from fastapi import APIRouter, Depends

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep, require_permissions
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.topic import topic_repository
from app.models.user import User
from app.services.debate_service import debate_service

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=dict[str, Any])
async def run_debate(
    db: DbDep,
    org_id: OrgIdDep,
    topic_id: int,
    question: str,
    provider_ids: list[int],
    current_user: User = Depends(require_permissions("topics:write")),
) -> Any:
    """Run an AI debate across multiple providers for a topic."""
    topic = await topic_repository.get_or_404_for_organization(db, topic_id, org_id)
    result = await debate_service.debate(
        db,
        topic=topic,
        question=question,
        provider_ids=provider_ids,
        user=current_user,
    )
    return result
