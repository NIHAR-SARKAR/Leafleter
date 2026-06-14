"""Report comment repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.report_comment import ReportComment

logger = get_logger(__name__)


class ReportCommentRepository(BaseRepository[ReportComment]):
    """Repository for report comments."""

    def __init__(self) -> None:
        super().__init__(ReportComment)

    async def get_by_report(
        self,
        db: AsyncSession,
        report_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ReportComment]:
        """List comments for a report."""
        result = await db.execute(
            select(ReportComment)
            .where(
                ReportComment.report_id == report_id,
                ReportComment.deleted_at.is_(None),
            )
            .order_by(ReportComment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


report_comment_repository = ReportCommentRepository()
