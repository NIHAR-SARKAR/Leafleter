"""Facebook Messenger notification channel stub."""

from typing import Any

from app.core.logging import get_logger
from app.notifications.base import NotificationChannel, NotificationResult

logger = get_logger(__name__)


class MessengerChannel(NotificationChannel):
    """Placeholder for Facebook Messenger integration."""

    name = "messenger"

    async def send(
        self,
        recipient: str,
        subject: str | None = None,
        body: str | None = None,
        **kwargs: Any,
    ) -> NotificationResult:
        """Stub delivery for Messenger messages."""
        logger.warning("messenger_channel_not_implemented", recipient=recipient)
        return NotificationResult(
            success=False, error="Messenger channel is not implemented"
        )
