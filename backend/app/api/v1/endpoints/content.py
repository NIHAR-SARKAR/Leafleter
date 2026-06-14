"""Content generator endpoints."""

from typing import Any

from fastapi import APIRouter, Depends

from app.core.deps import ActiveUserDep, DbDep, require_permissions
from app.core.logging import get_logger
from app.models.user import User
from app.services.content_service import content_service

logger = get_logger(__name__)
router = APIRouter()


@router.post("/generate", response_model=dict[str, str])
async def generate_content(
    db: DbDep,
    content_type: str,
    topic: str,
    tone: str = "professional",
    provider_id: int | None = None,
    current_user: User = Depends(require_permissions("topics:write")),
) -> Any:
    """Generate marketing content for a topic."""
    result = await content_service.generate(
        db,
        content_type=content_type,
        topic=topic,
        tone=tone,
        user=current_user,
        provider_id=provider_id,
    )
    return result
