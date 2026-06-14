"""Report comment endpoints for team collaboration."""

from typing import Any

from fastapi import APIRouter, Depends, status

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep, require_permissions
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.crud.report_comment import report_comment_repository
from app.models.report import Report
from app.models.user import User
from app.schemas.report_comment import ReportCommentCreate, ReportCommentInDB

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{report_id}/comments", response_model=list[ReportCommentInDB])
async def list_comments(
    db: DbDep,
    org_id: OrgIdDep,
    report_id: int,
    current_user: ActiveUserDep,
) -> Any:
    """List comments on a report."""
    repo = BaseRepository(Report)
    report = await repo.get_or_404(db, report_id)
    if report.organization_id != org_id:
        raise ForbiddenException("Access denied")
    return await report_comment_repository.get_by_report(db, report_id)


@router.post(
    "/{report_id}/comments",
    response_model=ReportCommentInDB,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    db: DbDep,
    org_id: OrgIdDep,
    report_id: int,
    obj_in: ReportCommentCreate,
    current_user: User = Depends(require_permissions("reports:write")),
) -> Any:
    """Add a comment to a report."""
    repo = BaseRepository(Report)
    report = await repo.get_or_404(db, report_id)
    if report.organization_id != org_id:
        raise ForbiddenException("Access denied")

    comment = await report_comment_repository.create(
        db,
        obj_in={
            "content": obj_in.content,
            "report_id": report.id,
            "user_id": current_user.id,
            "organization_id": org_id,
        },
    )
    await db.commit()
    await db.refresh(comment)
    return comment
