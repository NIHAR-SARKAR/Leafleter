"""Event bus for the Intelligence Core.

Supports direct event-type subscriptions, regex pattern subscriptions,
persistent event storage, and a background listener thread that delivers
events to subscribers.
"""

from __future__ import annotations

import asyncio
import logging
import re
import threading
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from queue import Queue
from typing import Any, Callable

from .database import SQLiteConnectionPool, deserialize_json, serialize_json

logger = logging.getLogger(__name__)


@dataclass
class _Subscription:
    """Internal representation of a subscriber."""

    callback: Callable[[dict], Any]
    pattern: re.Pattern | None = None
    is_async: bool = False


class EventBus:
    """In-memory + persistent event bus for cross-module intelligence events."""

    def __init__(self, db_path: str = "data/intelligence.db") -> None:
        self.db_path = db_path
        self._pool = SQLiteConnectionPool(db_path)
        self.subscribers: defaultdict[str, list[Callable[[dict], Any]]] = defaultdict(list)
        self.pattern_subscribers: list[_Subscription] = []
        self._lock = threading.Lock()
        self._running = False
        self._listener_thread: threading.Thread | None = None
        self._inbox: Queue[dict] = Queue()

    def publish(
        self,
        event_type: str,
        source: str,
        payload: dict,
        priority: str = "normal",
    ) -> str:
        """Persist and enqueue an event."""
        event_id = str(uuid.uuid4())
        event = {
            "id": event_id,
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "source": source,
            "payload": payload,
            "priority": priority,
        }
        try:
            self._pool.execute(
                """
                INSERT INTO events (id, type, source, payload_json, priority, processed)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_id, event_type, source, serialize_json(payload), priority, False),
            )
            logger.info(
                "event_published event_id=%s type=%s source=%s priority=%s",
                event_id, event_type, source, priority,
            )
            self._inbox.put(event)
        except Exception as exc:
            logger.error(f"event_publish_failed error={exc}")
        return event_id

    def subscribe(self, event_type: str, callback: Callable[[dict], Any]) -> None:
        """Subscribe ``callback`` to events of ``event_type``."""
        with self._lock:
            self.subscribers[event_type].append(callback)
        logger.info(f"event_subscribed event_type={event_type}")

    def subscribe_pattern(self, pattern: str, callback: Callable[[dict], Any]) -> None:
        """Subscribe ``callback`` to events whose type matches ``pattern``."""
        with self._lock:
            compiled = re.compile(pattern)
            is_async = asyncio.iscoroutinefunction(callback)
            self.pattern_subscribers.append(_Subscription(callback, compiled, is_async))
        logger.info(f"pattern_subscribed pattern={pattern}")

    def get_recent_events(
        self,
        hours: int = 24,
        source: str | None = None,
        event_type: str | None = None,
    ) -> list[dict]:
        """Return recent persisted events with optional filters."""
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        conditions = ["created_at >= ?"]
        params: list[Any] = [since]
        if source:
            conditions.append("source = ?")
            params.append(source)
        if event_type:
            conditions.append("type = ?")
            params.append(event_type)

        where_clause = " AND ".join(conditions)
        rows = self._pool.fetchall(
            f"""
            SELECT id, type, source, payload_json, priority, processed, created_at
            FROM events
            WHERE {where_clause}
            ORDER BY created_at DESC
            """,
            tuple(params),
        )
        return [self._row_to_event(row) for row in rows]

    def get_event_history(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 50,
    ) -> list[dict]:
        """Return events whose payload references a given entity."""
        rows = self._pool.fetchall(
            """
            SELECT id, type, source, payload_json, priority, processed, created_at
            FROM events
            WHERE payload_json LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (f'%"{entity_id}"%', limit),
        )
        return [self._row_to_event(row) for row in rows]

    def mark_processed(self, event_id: str) -> bool:
        """Mark an event as processed."""
        try:
            self._pool.execute(
                "UPDATE events SET processed = TRUE WHERE id = ?",
                (event_id,),
            )
            return True
        except Exception as exc:
            logger.error(f"mark_processed_failed error={exc}")
            return False

    def start_listener(self) -> None:
        """Start the background delivery thread."""
        if self._running:
            return
        self._running = True
        self._listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
        self._listener_thread.start()
        logger.info("event_bus_listener_started")

    def stop_listener(self) -> None:
        """Stop the background delivery thread."""
        self._running = False
        if self._listener_thread:
            self._inbox.put(None)
            self._listener_thread.join(timeout=5.0)
            logger.info("event_bus_listener_stopped")

    def _listener_loop(self) -> None:
        """Deliver events to subscribers."""
        while self._running:
            event = self._inbox.get()
            if event is None:
                break
            try:
                self._deliver(event)
                self.mark_processed(event["id"])
            except Exception as exc:
                logger.error(f"event_delivery_failed event_id={event["id"]} error={exc}")

    def _deliver(self, event: dict) -> None:
        """Invoke all matching subscribers for an event."""
        with self._lock:
            direct = list(self.subscribers.get(event["type"], []))
            patterns = list(self.pattern_subscribers)

        for callback in direct:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.run_coroutine_threadsafe(callback(event), asyncio.get_event_loop())
                else:
                    callback(event)
            except Exception as exc:
                logger.error(f"subscriber_callback_failed error={exc}")

        for subscription in patterns:
            if subscription.pattern and subscription.pattern.match(event["type"]):
                try:
                    if subscription.is_async:
                        asyncio.run_coroutine_threadsafe(subscription.callback(event), asyncio.get_event_loop())
                    else:
                        subscription.callback(event)
                except Exception as exc:
                    logger.error(f"pattern_subscriber_callback_failed error={exc}")

    def health_check(self) -> dict:
        """Return a simple health status for the event bus."""
        try:
            return {
                "status": "ok",
                "running": self._running,
                "subscribers": sum(len(v) for v in self.subscribers.values()),
                "pattern_subscribers": len(self.pattern_subscribers),
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def _row_to_event(self, row: dict) -> dict:
        return {
            "id": row["id"],
            "type": row["type"],
            "source": row["source"],
            "payload": deserialize_json(row["payload_json"], {}),
            "priority": row["priority"],
            "processed": bool(row["processed"]),
            "timestamp": row["created_at"],
        }
