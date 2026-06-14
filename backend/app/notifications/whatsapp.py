"""WhatsApp notification channel stub."""

from typing import Any

from app.core.logging import get_logger
from app.notifications.base import BaseNotificationChannel, NotificationMessage

logger = get_logger(__name__)


class WhatsAppNotificationChannel(BaseNotificationChannel):
    """WhatsApp notification channel (stub)."""

    channel_type = "whatsapp"

    async def send(self, message: NotificationMessage) -> dict[str, Any]:
        """Stub for WhatsApp notifications."""
        self._log_send(message)
        logger.warning("whatsapp_not_implemented")
        return {"status": "skipped", "reason": "WhatsApp channel not implemented"}
