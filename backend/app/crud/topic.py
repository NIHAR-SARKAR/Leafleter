"""Topic workspace repositories."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.topic import AnalysisResult, AnalysisRun, Topic, TopicSource

logger = get_logger(__name__)


class TopicRepository(BaseRepository[Topic]):
    """Repository for topic workspaces."""

    def __init__(self) -> None:
        super().__init__(Topic)

    async def get_or_404_for_organization(
        self,
        db: AsyncSession,
        topic_id: int,
        organization_id: int,
    ) -> Topic:
        """Fetch a topic ensuring it belongs to the organization."""
        topic = await self.get(db, topic_id)
        if topic is None or topic.organization_id != organization_id:
            raise NotFoundException("Topic not found")
        return topic

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        organization_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
        filters: dict | None = None,
        order_by=None,
    ) -> Sequence[Topic]:
        """List topics with mandatory tenant isolation."""
        return await super().get_multi(
            db,
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            filters=filters,
            order_by=order_by,
        )


class TopicSourceRepository(BaseRepository[TopicSource]):
    """Repository for topic data sources."""

    def __init__(self) -> None:
        super().__init__(TopicSource)

    async def get_by_topic(
        self,
        db: AsyncSession,
        topic_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[TopicSource]:
        """List sources attached to a topic."""
        result = await db.execute(
            select(TopicSource)
            .where(
                TopicSource.topic_id == topic_id,
                TopicSource.deleted_at.is_(None),
            )
            .order_by(TopicSource.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


class AnalysisRunRepository(BaseRepository[AnalysisRun]):
    """Repository for analysis run records."""

    def __init__(self) -> None:
        super().__init__(AnalysisRun)

    async def get_by_topic(
        self,
        db: AsyncSession,
        topic_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AnalysisRun]:
        """List analysis runs for a topic."""
        result = await db.execute(
            select(AnalysisRun)
            .where(
                AnalysisRun.topic_id == topic_id,
                AnalysisRun.deleted_at.is_(None),
            )
            .order_by(AnalysisRun.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


class AnalysisResultRepository(BaseRepository[AnalysisResult]):
    """Repository for analysis result records."""

    def __init__(self) -> None:
        super().__init__(AnalysisResult)

    async def get_by_run(
        self,
        db: AsyncSession,
        run_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AnalysisResult]:
        """List results for an analysis run."""
        result = await db.execute(
            select(AnalysisResult)
            .where(
                AnalysisResult.run_id == run_id,
                AnalysisResult.deleted_at.is_(None),
            )
            .order_by(AnalysisResult.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


# Global repository instances.
topic_repository = TopicRepository()
topic_source_repository = TopicSourceRepository()
analysis_run_repository = AnalysisRunRepository()
analysis_result_repository = AnalysisResultRepository()
