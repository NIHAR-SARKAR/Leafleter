"""Competitor endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, status

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep, require_permissions
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.competitor import competitor_repository, competitor_snapshot_repository
from app.models.user import User
from app.schemas.competitor import (
    CompetitorCreate,
    CompetitorInDB,
    CompetitorPublic,
    CompetitorSnapshotInDB,
    CompetitorUpdate,
)
from app.services.competitor_service import competitor_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=list[CompetitorInDB])
async def list_competitors(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List competitors for the organization."""
    competitors = await competitor_repository.get_active_by_organization(
        db, org_id, skip=skip, limit=limit
    )
    return competitors


@router.post("", response_model=CompetitorInDB, status_code=status.HTTP_201_CREATED)
async def create_competitor(
    db: DbDep,
    org_id: OrgIdDep,
    obj_in: CompetitorCreate,
    current_user: User = Depends(require_permissions("topics:write")),
) -> Any:
    """Create a competitor."""
    competitor = await competitor_service.create(
        db, obj_in=obj_in, user=current_user
    )
    return competitor


@router.get("/{competitor_id}", response_model=CompetitorPublic)
async def get_competitor(
    db: DbDep,
    org_id: OrgIdDep,
    competitor_id: int,
    current_user: ActiveUserDep,
) -> Any:
    """Get a competitor with snapshots."""
    competitor = await competitor_repository.get_or_404(db, competitor_id)
    if competitor.organization_id != org_id:
        raise ForbiddenException("Access denied")
    return competitor


@router.put("/{competitor_id}", response_model=CompetitorInDB)
async def update_competitor(
    db: DbDep,
    org_id: OrgIdDep,
    competitor_id: int,
    obj_in: CompetitorUpdate,
    current_user: User = Depends(require_permissions("topics:write")),
) -> Any:
    """Update a competitor."""
    competitor = await competitor_repository.get_or_404(db, competitor_id)
    if competitor.organization_id != org_id:
        raise ForbiddenException("Access denied")
    competitor = await competitor_service.update(
        db, competitor=competitor, obj_in=obj_in
    )
    return competitor


@router.delete("/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_competitor(
    db: DbDep,
    org_id: OrgIdDep,
    competitor_id: int,
    current_user: User = Depends(require_permissions("topics:write")),
) -> None:
    """Delete a competitor."""
    competitor = await competitor_repository.get_or_404(db, competitor_id)
    if competitor.organization_id != org_id:
        raise ForbiddenException("Access denied")
    await competitor_service.delete(db, competitor=competitor)
    return None


@router.post("/{competitor_id}/snapshots", response_model=CompetitorSnapshotInDB)
async def take_snapshot(
    db: DbDep,
    org_id: OrgIdDep,
    competitor_id: int,
    snapshot_type: str = "website",
    current_user: User = Depends(require_permissions("topics:write")),
) -> Any:
    """Take a competitor snapshot."""
    competitor = await competitor_repository.get_or_404(db, competitor_id)
    if competitor.organization_id != org_id:
        raise ForbiddenException("Access denied")
    await competitor_service.take_snapshot(
        db, competitor=competitor, snapshot_type=snapshot_type
    )
    snapshots = await competitor_snapshot_repository.get_by_competitor(
        db, competitor.id, limit=1
    )
    return snapshots[0]


@router.get("/{competitor_id}/snapshots", response_model=list[CompetitorSnapshotInDB])
async def list_snapshots(
    db: DbDep,
    org_id: OrgIdDep,
    competitor_id: int,
    current_user: ActiveUserDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List competitor snapshots."""
    competitor = await competitor_repository.get_or_404(db, competitor_id)
    if competitor.organization_id != org_id:
        raise ForbiddenException("Access denied")
    snapshots = await competitor_snapshot_repository.get_by_competitor(
        db, competitor.id, skip=skip, limit=limit
    )
    return snapshots
