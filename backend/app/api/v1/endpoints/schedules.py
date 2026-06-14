"""Schedule endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Response, status

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep, require_permissions
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.schedule import Schedule
from app.models.user import User
from app.schemas.schedule import ScheduleCreate, ScheduleInDB, ScheduleUpdate
from app.services.scheduler_service import scheduler_service_app

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=list[ScheduleInDB])
async def list_schedules(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List schedules for the organization."""
    repo = BaseRepository(Schedule)
    schedules = await repo.get_multi(
        db, organization_id=org_id, skip=skip, limit=limit
    )
    return schedules


@router.post("", response_model=ScheduleInDB, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    db: DbDep,
    org_id: OrgIdDep,
    obj_in: ScheduleCreate,
    current_user: User = Depends(require_permissions("schedules:write")),
) -> Any:
    """Create a new schedule."""
    schedule = await scheduler_service_app.create_schedule(
        db, obj_in=obj_in, user=current_user
    )
    return schedule


@router.get("/{schedule_id}", response_model=ScheduleInDB)
async def get_schedule(
    db: DbDep,
    org_id: OrgIdDep,
    schedule_id: int,
    current_user: ActiveUserDep,
) -> Any:
    """Get a specific schedule."""
    repo = BaseRepository(Schedule)
    schedule = await repo.get_or_404(db, schedule_id)
    if schedule.organization_id != org_id:
        raise ForbiddenException("Access denied")
    return schedule


@router.put("/{schedule_id}", response_model=ScheduleInDB)
async def update_schedule(
    db: DbDep,
    org_id: OrgIdDep,
    schedule_id: int,
    obj_in: ScheduleUpdate,
    current_user: User = Depends(require_permissions("schedules:write")),
) -> Any:
    """Update a schedule."""
    repo = BaseRepository(Schedule)
    schedule = await repo.get_or_404(db, schedule_id)
    if schedule.organization_id != org_id:
        raise ForbiddenException("Access denied")
    schedule = await scheduler_service_app.update_schedule(
        db, schedule=schedule, obj_in=obj_in
    )
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    db: DbDep,
    org_id: OrgIdDep,
    schedule_id: int,
    current_user: User = Depends(require_permissions("schedules:write")),
) -> None:
    """Delete a schedule."""
    repo = BaseRepository(Schedule)
    schedule = await repo.get_or_404(db, schedule_id)
    if schedule.organization_id != org_id:
        raise ForbiddenException("Access denied")
    await scheduler_service_app.delete_schedule(db, schedule=schedule)
    return None
