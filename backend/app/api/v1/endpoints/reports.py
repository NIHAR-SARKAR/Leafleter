"""Report endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, status

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep, require_permissions
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportCreate, ReportInDB, ReportUpdate
from app.services.report_service import report_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=list[ReportInDB])
async def list_reports(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    topic_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List reports for the organization."""
    filters: dict[str, Any] = {}
    if topic_id:
        filters["topic_id"] = topic_id
    repo = BaseRepository(Report)
    reports = await repo.get_multi(
        db, organization_id=org_id, skip=skip, limit=limit, filters=filters
    )
    return reports


@router.post("", response_model=ReportInDB, status_code=status.HTTP_201_CREATED)
async def create_report(
    db: DbDep,
    org_id: OrgIdDep,
    obj_in: ReportCreate,
    current_user: User = Depends(require_permissions("reports:write")),
) -> Any:
    """Generate a new report."""
    report = await report_service.create_report(db, obj_in=obj_in, user=current_user)
    return report


@router.get("/{report_id}", response_model=ReportInDB)
async def get_report(
    db: DbDep,
    org_id: OrgIdDep,
    report_id: int,
    current_user: ActiveUserDep,
) -> Any:
    """Get a specific report."""
    repo = BaseRepository(Report)
    report = await repo.get_or_404(db, report_id)
    if report.organization_id != org_id:
        raise ForbiddenException("Access denied")
    return report


@router.put("/{report_id}", response_model=ReportInDB)
async def update_report(
    db: DbDep,
    org_id: OrgIdDep,
    report_id: int,
    obj_in: ReportUpdate,
    current_user: User = Depends(require_permissions("reports:write")),
) -> Any:
    """Update report metadata (e.g., approve)."""
    repo = BaseRepository(Report)
    report = await repo.get_or_404(db, report_id)
    if report.organization_id != org_id:
        raise ForbiddenException("Access denied")
    update_data = obj_in.model_dump(exclude_unset=True)
    if obj_in.is_approved:
        update_data["approved_by_user_id"] = current_user.id
    report = await repo.update(db, db_obj=report, obj_in=update_data)
    await db.commit()
    await db.refresh(report)
    return report
