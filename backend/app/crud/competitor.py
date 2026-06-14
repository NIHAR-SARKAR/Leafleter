"""Competitor repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.competitor import Competitor, CompetitorSnapshot

logger = get_logger(__name__)


class CompetitorRepository(BaseRepository[Competitor]):
    """Repository for competitors."""

    def __init__(self) -> None:
        super().__init__(Competitor)

    async def get_active_by_organization(
        self,
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Competitor]:
        """List active competitors for an organization."""
        result = await db.execute(
            select(Competitor)
            .where(
                Competitor.organization_id == organization_id,
                Competitor.deleted_at.is_(None),
            )
            .order_by(Competitor.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


class CompetitorSnapshotRepository(BaseRepository[CompetitorSnapshot]):
    """Repository for competitor snapshots."""

    def __init__(self) -> None:
        super().__init__(CompetitorSnapshot)

    async def get_by_competitor(
        self,
        db: AsyncSession,
        competitor_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CompetitorSnapshot]:
        """List snapshots for a competitor."""
        result = await db.execute(
            select(CompetitorSnapshot)
            .where(
                CompetitorSnapshot.competitor_id == competitor_id,
                CompetitorSnapshot.deleted_at.is_(None),
            )
            .order_by(CompetitorSnapshot.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


competitor_repository = CompetitorRepository()
competitor_snapshot_repository = CompetitorSnapshotRepository()
