"""Notification repository."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.notification import Notification

logger = get_logger(__name__)


class NotificationRepository(BaseRepository[Notification]):
    """Repository for outbound notification messages."""

    def __init__(self) -> None:
        super().__init__(Notification)

    async def get_by_organization(
        self,
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
        is_read: bool | None = None,
    ) -> Sequence[Notification]:
        """List notifications for an organization."""
        stmt = (
            select(Notification)
            .where(
                Notification.organization_id == organization_id,
                Notification.deleted_at.is_(None),
            )
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if is_read is not None:
            stmt = stmt.where(Notification.is_read.is_(is_read))
        result = await db.execute(stmt)
        return result.scalars().all()

    async def mark_read(
        self,
        db: AsyncSession,
        *,
        notification: Notification,
        is_read: bool = True,
    ) -> Notification:
        """Mark a notification as read or unread."""
        notification.is_read = is_read
        db.add(notification)
        await db.flush()
        await db.refresh(notification)
        return notification


notification_repository = NotificationRepository()
