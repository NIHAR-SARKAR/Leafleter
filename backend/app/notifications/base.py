"""Base notification channel."""

from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class NotificationMessage:
    """Standardized notification payload."""

    recipient: str
    subject: str
    body: str
    channel: str
    metadata: dict[str, Any] | None = None


class BaseNotificationChannel:
    """Abstract notification channel."""

    channel_type: str = ""

    async def send(self, message: NotificationMessage) -> dict[str, Any]:
        """Send a notification message."""
        raise NotImplementedError

    def _log_send(self, message: NotificationMessage) -> None:
        """Log a send attempt."""
        logger.info(
            "notification_send_attempt",
            channel=self.channel_type,
            recipient=message.recipient,
        )
