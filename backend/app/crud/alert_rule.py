"""Alert rule repository."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.alert import AlertRule

logger = get_logger(__name__)


class AlertRuleRepository(BaseRepository[AlertRule]):
    """Repository for automated alert rule definitions."""

    def __init__(self) -> None:
        super().__init__(AlertRule)

    async def get_by_organization(
        self,
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AlertRule]:
        """List alert rules for an organization."""
        result = await db.execute(
            select(AlertRule)
            .where(
                AlertRule.organization_id == organization_id,
                AlertRule.deleted_at.is_(None),
            )
            .order_by(AlertRule.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_active_by_organization(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Sequence[AlertRule]:
        """Return active alert rules for an organization."""
        result = await db.execute(
            select(AlertRule).where(
                AlertRule.organization_id == organization_id,
                AlertRule.is_active.is_(True),
                AlertRule.deleted_at.is_(None),
            )
        )
        return result.scalars().all()


alert_rule_repository = AlertRuleRepository()
