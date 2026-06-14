"""Schedule repository."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.schedule import Schedule

logger = get_logger(__name__)


class ScheduleRepository(BaseRepository[Schedule]):
    """Repository for scheduled job definitions."""

    def __init__(self) -> None:
        super().__init__(Schedule)

    async def get_by_organization(
        self,
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Schedule]:
        """List schedules for an organization."""
        result = await db.execute(
            select(Schedule)
            .where(
                Schedule.organization_id == organization_id,
                Schedule.deleted_at.is_(None),
            )
            .order_by(Schedule.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_active_by_organization(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Sequence[Schedule]:
        """Return active schedules that should be synced to the scheduler."""
        result = await db.execute(
            select(Schedule).where(
                Schedule.organization_id == organization_id,
                Schedule.is_active.is_(True),
                Schedule.deleted_at.is_(None),
            )
        )
        return result.scalars().all()

    async def update_next_run(
        self,
        db: AsyncSession,
        *,
        schedule: Schedule,
        last_run_at: Any,
        next_run_at: Any,
    ) -> Schedule:
        """Update schedule run timestamps."""
        schedule.last_run_at = last_run_at
        schedule.next_run_at = next_run_at
        db.add(schedule)
        await db.flush()
        await db.refresh(schedule)
        return schedule


schedule_repository = ScheduleRepository()
