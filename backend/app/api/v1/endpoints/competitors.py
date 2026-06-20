"""Competitor endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep, require_permissions
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.logging import get_logger
from app.crud.competitor import (
    competitor_feature_comparison_repository,
    competitor_repository,
    competitor_snapshot_repository,
)
from app.crud.organization import organization_repository
from app.models.user import User
from app.schemas.competitor import (
    CompetitorCreate,
    CompetitorFeatureComparisonCreate,
    CompetitorFeatureComparisonInDB,
    CompetitorFeatureComparisonPublic,
    CompetitorInDB,
    CompetitorPublic,
    CompetitorSnapshotInDB,
    CompetitorUpdate,
)
from app.services.competitor_feature_service import competitor_feature_service
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


@router.post(
    "/{competitor_id}/compare",
    response_model=CompetitorFeatureComparisonInDB,
    status_code=status.HTTP_202_ACCEPTED,
)
async def compare_competitor_features(
    db: DbDep,
    org_id: OrgIdDep,
    competitor_id: int,
    obj_in: CompetitorFeatureComparisonCreate | None = None,
    current_user: User = Depends(require_permissions("topics:write")),
) -> Any:
    """Generate a feature comparison report for a competitor."""
    competitor = await competitor_repository.get_or_404(db, competitor_id)
    if competitor.organization_id != org_id:
        raise ForbiddenException("Access denied")

    organization = await organization_repository.get_or_404(db, org_id)
    comparison = await competitor_feature_service.run_comparison(
        db,
        competitor=competitor,
        organization=organization,
        user=current_user,
        obj_in=obj_in,
    )
    return comparison


@router.get(
    "/{competitor_id}/comparisons",
    response_model=list[CompetitorFeatureComparisonInDB],
)
async def list_competitor_comparisons(
    db: DbDep,
    org_id: OrgIdDep,
    competitor_id: int,
    current_user: ActiveUserDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List feature comparison reports for a competitor."""
    competitor = await competitor_repository.get_or_404(db, competitor_id)
    if competitor.organization_id != org_id:
        raise ForbiddenException("Access denied")
    comparisons = await competitor_feature_comparison_repository.get_by_competitor(
        db, competitor.id, skip=skip, limit=limit
    )
    return comparisons


@router.get(
    "/{competitor_id}/comparisons/latest",
    response_model=CompetitorFeatureComparisonPublic,
)
async def get_latest_comparison(
    db: DbDep,
    org_id: OrgIdDep,
    competitor_id: int,
    current_user: ActiveUserDep,
) -> Any:
    """Return the latest feature comparison report for a competitor."""
    competitor = await competitor_repository.get_or_404(db, competitor_id)
    if competitor.organization_id != org_id:
        raise ForbiddenException("Access denied")
    comparison = await competitor_feature_comparison_repository.get_latest_by_competitor(
        db, competitor.id
    )
    if comparison is None:
        raise NotFoundException("No comparison report found")
    return comparison


@router.get(
    "/comparisons/{comparison_id}/download",
    response_class=FileResponse,
)
async def download_comparison_report(
    db: DbDep,
    org_id: OrgIdDep,
    comparison_id: int,
    current_user: ActiveUserDep,
) -> Any:
    """Download a comparison report DOCX file."""
    comparison = await competitor_feature_comparison_repository.get_or_404(
        db, comparison_id
    )
    if comparison.organization_id != org_id:
        raise ForbiddenException("Access denied")
    if not comparison.file_path or not comparison.download_url:
        raise NotFoundException("Report file not available")
    return FileResponse(
        path=comparison.file_path,
        filename=f"{comparison.title.replace(' ', '_')}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
