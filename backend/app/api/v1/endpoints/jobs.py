"""Job monitoring endpoints."""

from typing import Any

from fastapi import APIRouter

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.job import Job
from app.schemas.schedule import JobInDB

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=list[JobInDB])
async def list_jobs(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List jobs for the organization."""
    repo = BaseRepository(Job)
    jobs = await repo.get_multi(db, organization_id=org_id, skip=skip, limit=limit)
    return jobs


@router.get("/{job_id}", response_model=JobInDB)
async def get_job(
    db: DbDep,
    org_id: OrgIdDep,
    job_id: int,
    current_user: ActiveUserDep,
) -> Any:
    """Get a specific job."""
    repo = BaseRepository(Job)
    job = await repo.get_or_404(db, job_id)
    if job.organization_id != org_id:
        raise ForbiddenException("Access denied")
    return job
