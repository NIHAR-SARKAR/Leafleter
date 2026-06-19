"""Competitor repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.competitor import Competitor, CompetitorFeatureComparison, CompetitorSnapshot

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

    async def get_latest_by_type(
        self,
        db: AsyncSession,
        competitor_id: int,
        snapshot_type: str,
    ) -> CompetitorSnapshot | None:
        """Return the most recent snapshot of a given type for a competitor."""
        result = await db.execute(
            select(CompetitorSnapshot)
            .where(
                CompetitorSnapshot.competitor_id == competitor_id,
                CompetitorSnapshot.snapshot_type == snapshot_type,
                CompetitorSnapshot.deleted_at.is_(None),
            )
            .order_by(CompetitorSnapshot.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class CompetitorFeatureComparisonRepository(BaseRepository[CompetitorFeatureComparison]):
    """Repository for competitor feature comparisons."""

    def __init__(self) -> None:
        super().__init__(CompetitorFeatureComparison)

    async def get_by_competitor(
        self,
        db: AsyncSession,
        competitor_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CompetitorFeatureComparison]:
        """List feature comparisons for a competitor."""
        result = await db.execute(
            select(CompetitorFeatureComparison)
            .where(
                CompetitorFeatureComparison.competitor_id == competitor_id,
                CompetitorFeatureComparison.deleted_at.is_(None),
            )
            .order_by(CompetitorFeatureComparison.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_by_competitor(
        self,
        db: AsyncSession,
        competitor_id: int,
    ) -> CompetitorFeatureComparison | None:
        """Return the most recent feature comparison for a competitor."""
        result = await db.execute(
            select(CompetitorFeatureComparison)
            .where(
                CompetitorFeatureComparison.competitor_id == competitor_id,
                CompetitorFeatureComparison.deleted_at.is_(None),
            )
            .order_by(CompetitorFeatureComparison.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


competitor_repository = CompetitorRepository()
competitor_snapshot_repository = CompetitorSnapshotRepository()
competitor_feature_comparison_repository = CompetitorFeatureComparisonRepository()
