"""Notification dispatch service."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.notification import Notification
from app.models.user import User
from app.notifications.base import NotificationMessage
from app.notifications.discord import DiscordNotificationChannel
from app.notifications.email import EmailNotificationChannel
from app.notifications.slack import SlackNotificationChannel
from app.notifications.teams import TeamsNotificationChannel
from app.notifications.whatsapp import WhatsAppNotificationChannel
from app.schemas.notification import NotificationCreate

logger = get_logger(__name__)

CHANNEL_MAP: dict[str, type] = {
    "email": EmailNotificationChannel,
    "slack": SlackNotificationChannel,
    "teams": TeamsNotificationChannel,
    "discord": DiscordNotificationChannel,
    "whatsapp": WhatsAppNotificationChannel,
    "messenger": WhatsAppNotificationChannel,
}


class NotificationService:
    """Service for creating and dispatching notifications."""

    async def send_notification(
        self,
        db: AsyncSession,
        *,
        obj_in: NotificationCreate,
        organization_id: int,
        user_id: int | None = None,
    ) -> Notification:
        """Create a notification record and dispatch it."""
        repo = BaseRepository(Notification)
        notification = await repo.create(
            db,
            obj_in={
                **obj_in.model_dump(),
                "organization_id": organization_id,
                "user_id": user_id,
                "status": "pending",
            },
        )
        await db.commit()
        await db.refresh(notification)

        channel_class = CHANNEL_MAP.get(obj_in.channel)
        if channel_class is None:
            notification.status = "failed"
            notification.error_message = "Unknown channel"
            await db.commit()
            return notification

        channel = channel_class()
        message = NotificationMessage(
            recipient=obj_in.recipient,
            subject=obj_in.subject or "",
            body=obj_in.body or "",
            channel=obj_in.channel,
            metadata=obj_in.metadata,
        )
        notification.sent_at = datetime.now(timezone.utc)
        result = await channel.send(message)
        notification.status = result.get("status", "failed")
        if notification.status == "failed":
            notification.error_message = result.get("error", "Unknown error")
        notification.delivered_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(notification)
        return notification

    async def send_to_user(
        self,
        db: AsyncSession,
        *,
        user: User,
        subject: str,
        body: str,
        channel: str = "email",
    ) -> Notification:
        """Send a notification to a user."""
        from app.schemas.notification import NotificationCreate

        return await self.send_notification(
            db,
            obj_in=NotificationCreate(
                channel=channel,
                recipient=user.email,
                subject=subject,
                body=body,
            ),
            organization_id=user.organization_id,
            user_id=user.id,
        )


notification_service = NotificationService()
