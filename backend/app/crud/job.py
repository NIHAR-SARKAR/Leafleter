"""Job execution repository."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.job import Job

logger = get_logger(__name__)


class JobRepository(BaseRepository[Job]):
    """Repository for job execution records."""

    def __init__(self) -> None:
        super().__init__(Job)

    async def get_by_organization(
        self,
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
    ) -> Sequence[Job]:
        """List job executions for an organization."""
        stmt = (
            select(Job)
            .where(
                Job.organization_id == organization_id,
                Job.deleted_at.is_(None),
            )
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if status is not None:
            stmt = stmt.where(Job.status == status)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_schedule(
        self,
        db: AsyncSession,
        schedule_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Job]:
        """List job executions for a schedule."""
        result = await db.execute(
            select(Job)
            .where(
                Job.schedule_id == schedule_id,
                Job.deleted_at.is_(None),
            )
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


job_repository = JobRepository()
