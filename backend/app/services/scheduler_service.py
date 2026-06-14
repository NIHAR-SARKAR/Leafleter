"""Schedule management service."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.job import Job
from app.models.schedule import Schedule
from app.models.user import User
from app.scheduler.jobs import execute_job
from app.scheduler.scheduler import scheduler_service
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate

logger = get_logger(__name__)


class SchedulerService:
    """Service for managing scheduled jobs and APScheduler sync."""

    async def create_schedule(
        self,
        db: AsyncSession,
        *,
        obj_in: ScheduleCreate,
        user: User,
    ) -> Schedule:
        """Create a schedule and register it with APScheduler."""
        repo = BaseRepository(Schedule)
        schedule = await repo.create(
            db,
            obj_in={
                **obj_in.model_dump(),
                "organization_id": user.organization_id,
                "created_by_id": user.id,
                "is_active": True,
            },
        )
        await db.commit()
        await db.refresh(schedule)
        await self._sync_to_scheduler(db, schedule=schedule)
        logger.info("schedule_created", schedule_id=schedule.id)
        return schedule

    async def update_schedule(
        self,
        db: AsyncSession,
        *,
        schedule: Schedule,
        obj_in: ScheduleUpdate,
    ) -> Schedule:
        """Update a schedule and re-register with APScheduler."""
        repo = BaseRepository(Schedule)
        schedule = await repo.update(
            db, db_obj=schedule, obj_in=obj_in.model_dump(exclude_unset=True)
        )
        await db.commit()
        await db.refresh(schedule)
        await self._sync_to_scheduler(db, schedule=schedule)
        return schedule

    async def delete_schedule(
        self,
        db: AsyncSession,
        *,
        schedule: Schedule,
    ) -> None:
        """Delete a schedule and remove from APScheduler."""
        if scheduler_service.scheduler:
            try:
                scheduler_service.remove_job(f"schedule_{schedule.id}")
            except Exception:
                pass
        repo = BaseRepository(Schedule)
        await repo.delete(db, db_obj=schedule)
        await db.commit()

    async def _sync_to_scheduler(self, db: AsyncSession, schedule: Schedule) -> None:
        """Register or update the APScheduler job for a schedule."""
        if not scheduler_service.scheduler or not schedule.is_active:
            return

        job_id = f"schedule_{schedule.id}"
        try:
            scheduler_service.remove_job(job_id)
        except Exception:
            pass

        async def job_wrapper() -> None:
            from app.db.session import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                job_record = await BaseRepository(Job).create(
                    session,
                    obj_in={
                        "job_type": schedule.job_type,
                        "status": "pending",
                        "schedule_id": schedule.id,
                        "organization_id": schedule.organization_id,
                    },
                )
                await session.commit()
                await execute_job(
                    session,
                    job_id=job_record.id,
                    job_type=schedule.job_type,
                    organization_id=schedule.organization_id,
                    config=schedule.configuration or {},
                )

        scheduler_service.scheduler.add_job(
            job_wrapper,
            trigger="cron",
            id=job_id,
            replace_existing=True,
            **self._parse_cron(schedule.cron_expression),
            timezone=schedule.timezone,
        )
        schedule.next_run_at = datetime.now(timezone.utc)  # Approximate
        db.add(schedule)
        await db.commit()

    def _parse_cron(self, cron_expression: str) -> dict[str, Any]:
        """Parse a cron expression into APScheduler kwargs.

        Supports standard 5-field cron: minute hour day month day_of_week.
        """
        parts = cron_expression.split()
        if len(parts) != 5:
            raise AppException("Invalid cron expression; expected 5 fields")
        return {
            "minute": parts[0],
            "hour": parts[1],
            "day": parts[2],
            "month": parts[3],
            "day_of_week": parts[4],
        }


scheduler_service_app = SchedulerService()
