"""Alert endpoints."""

from typing import Any

from fastapi import APIRouter

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.alert import Alert
from app.schemas.alert import AlertInDB

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=list[AlertInDB])
async def list_alerts(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List alerts for the organization."""
    repo = BaseRepository(Alert)
    alerts = await repo.get_multi(db, organization_id=org_id, skip=skip, limit=limit)
    return alerts


@router.get("/{alert_id}", response_model=AlertInDB)
async def get_alert(
    db: DbDep,
    org_id: OrgIdDep,
    alert_id: int,
    current_user: ActiveUserDep,
) -> Any:
    """Get a specific alert."""
    repo = BaseRepository(Alert)
    alert = await repo.get_or_404(db, alert_id)
    if alert.organization_id != org_id:
        raise ForbiddenException("Access denied")
    return alert
