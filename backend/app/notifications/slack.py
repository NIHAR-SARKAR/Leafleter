"""Slack webhook notification channel."""

from typing import Any

import httpx

from app.core.logging import get_logger
from app.notifications.base import BaseNotificationChannel, NotificationMessage

logger = get_logger(__name__)


class SlackNotificationChannel(BaseNotificationChannel):
    """Slack incoming webhook notification channel."""

    channel_type = "slack"

    async def send(self, message: NotificationMessage) -> dict[str, Any]:
        """Send a Slack notification via webhook URL."""
        self._log_send(message)
        webhook_url = (message.metadata or {}).get("webhook_url")
        if not webhook_url:
            return {"status": "skipped", "reason": "Missing webhook URL"}

        payload = {
            "text": f"*{message.subject}*\n{message.body}",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(webhook_url, json=payload)
                response.raise_for_status()
                return {"status": "sent"}
            except Exception as exc:
                logger.error("slack_send_failed", error=str(exc))
                return {"status": "failed", "error": str(exc)}
