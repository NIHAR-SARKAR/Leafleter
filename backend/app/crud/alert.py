"""Alert repository."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.alert import Alert

logger = get_logger(__name__)


class AlertRepository(BaseRepository[Alert]):
    """Repository for triggered alert instances."""

    def __init__(self) -> None:
        super().__init__(Alert)

    async def get_by_organization(
        self,
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
    ) -> Sequence[Alert]:
        """List alerts for an organization."""
        stmt = (
            select(Alert)
            .where(
                Alert.organization_id == organization_id,
                Alert.deleted_at.is_(None),
            )
            .order_by(Alert.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if status is not None:
            stmt = stmt.where(Alert.status == status)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def acknowledge(
        self,
        db: AsyncSession,
        *,
        alert: Alert,
        user_id: int,
    ) -> Alert:
        """Mark an alert as acknowledged by a user."""
        alert.status = "acknowledged"
        alert.acknowledged_by_user_id = user_id
        db.add(alert)
        await db.flush()
        await db.refresh(alert)
        return alert


alert_repository = AlertRepository()
