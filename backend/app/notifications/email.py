"""Email notification channel via SMTP."""

from typing import Any

import aiosmtplib

from app.core.config import settings
from app.core.logging import get_logger
from app.notifications.base import BaseNotificationChannel, NotificationMessage

logger = get_logger(__name__)


class EmailNotificationChannel(BaseNotificationChannel):
    """SMTP email notification channel."""

    channel_type = "email"

    async def send(self, message: NotificationMessage) -> dict[str, Any]:
        """Send an email via SMTP."""
        self._log_send(message)
        if not settings.SMTP_HOST:
            logger.warning("smtp_not_configured")
            return {"status": "skipped", "reason": "SMTP not configured"}

        try:
            await aiosmtplib.send(
                message=message.body,
                subject=message.subject,
                sender=settings.SMTP_FROM or settings.SMTP_USER,
                recipients=[message.recipient],
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT or 587,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )
            return {"status": "sent"}
        except Exception as exc:
            logger.error("email_send_failed", error=str(exc))
            return {"status": "failed", "error": str(exc)}
