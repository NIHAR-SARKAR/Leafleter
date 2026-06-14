"""Competitor intelligence service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.competitor import competitor_repository, competitor_snapshot_repository
from app.models.competitor import Competitor
from app.models.user import User
from app.schemas.competitor import CompetitorCreate, CompetitorUpdate
from app.services.intelligence_hooks import (
    on_competitor_created,
    on_competitor_deleted,
    on_competitor_updated,
)
from app.services.search_service import search_service

logger = get_logger(__name__)


class CompetitorService:
    """Service for competitor tracking and snapshots."""

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CompetitorCreate,
        user: User,
    ) -> Competitor:
        """Create a competitor record."""
        competitor = await competitor_repository.create(
            db,
            obj_in={
                **obj_in.model_dump(),
                "organization_id": user.organization_id,
                "is_active": True,
            },
        )
        await db.commit()
        await db.refresh(competitor)
        logger.info("competitor_created", competitor_id=competitor.id)
        try:
            on_competitor_created(competitor)
        except Exception as exc:
            logger.warning("intelligence_competitor_created_hook_failed", error=str(exc))
        return competitor

    async def update(
        self,
        db: AsyncSession,
        *,
        competitor: Competitor,
        obj_in: CompetitorUpdate,
    ) -> Competitor:
        """Update a competitor."""
        competitor = await competitor_repository.update(
            db, db_obj=competitor, obj_in=obj_in.model_dump(exclude_unset=True)
        )
        await db.commit()
        await db.refresh(competitor)
        try:
            on_competitor_updated(competitor)
        except Exception as exc:
            logger.warning("intelligence_competitor_updated_hook_failed", error=str(exc))
        return competitor

    async def delete(self, db: AsyncSession, *, competitor: Competitor) -> None:
        """Soft delete a competitor."""
        competitor_id = competitor.id
        await competitor_repository.delete(db, db_obj=competitor)
        await db.commit()
        try:
            on_competitor_deleted(competitor_id)
        except Exception as exc:
            logger.warning("intelligence_competitor_deleted_hook_failed", error=str(exc))

    async def take_snapshot(
        self,
        db: AsyncSession,
        *,
        competitor: Competitor,
        snapshot_type: str = "website",
    ) -> Competitor:
        """Take a snapshot of competitor data."""
        content = ""
        if competitor.website_url and snapshot_type == "website":
            try:
                result = await search_service.crawl(competitor.website_url)
                content = result.text[:5000]
            except Exception as exc:
                logger.warning("competitor_snapshot_crawl_failed", error=str(exc))

        await competitor_snapshot_repository.create(
            db,
            obj_in={
                "competitor_id": competitor.id,
                "snapshot_type": snapshot_type,
                "source_url": competitor.website_url,
                "content": content,
                "metrics": {},
            },
        )
        await db.commit()
        return competitor


competitor_service = CompetitorService()
