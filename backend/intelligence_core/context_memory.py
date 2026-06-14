"""Context memory for the Intelligence Core.

Stores per-session, per-module context so that AI responses can be enriched
with recent events, entity relationships, and prior conversation history.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .database import SQLiteConnectionPool, deserialize_json, serialize_json

if TYPE_CHECKING:
    from .entity_graph import EntityGraph

logger = logging.getLogger(__name__)


class ContextMemory:
    """Session-scoped memory for AI context enrichment."""

    def __init__(self, db_path: str = "data/intelligence.db") -> None:
        self.db_path = db_path
        self._pool = SQLiteConnectionPool(db_path)

    def store_context(self, session_id: str, module: str, context_data: dict) -> bool:
        """Persist context data for a session/module pair."""
        try:
            now = datetime.utcnow().isoformat()
            self._pool.execute(
                """
                INSERT INTO context_sessions (session_id, module, context_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id, module) DO UPDATE SET
                    context_json = excluded.context_json,
                    updated_at = excluded.updated_at
                """,
                (session_id, module, serialize_json(context_data), now),
            )
            logger.info(f"context_stored session_id={session_id} module={module}")
            return True
        except Exception as exc:
            logger.error(f"context_store_failed error={exc}")
            return False

    def get_context(self, session_id: str, module: str | None = None) -> dict[str, Any]:
        """Return context for a session, optionally filtered by module."""
        try:
            if module:
                row = self._pool.fetchone(
                    """
                    SELECT module, context_json, updated_at
                    FROM context_sessions
                    WHERE session_id = ? AND module = ?
                    """,
                    (session_id, module),
                )
                if not row:
                    return {}
                return {
                    row["module"]: {
                        "context": deserialize_json(row["context_json"], {}),
                        "updated_at": row["updated_at"],
                    }
                }

            rows = self._pool.fetchall(
                """
                SELECT module, context_json, updated_at
                FROM context_sessions
                WHERE session_id = ?
                ORDER BY updated_at DESC
                """,
                (session_id,),
            )
            return {
                row["module"]: {
                    "context": deserialize_json(row["context_json"], {}),
                    "updated_at": row["updated_at"],
                }
                for row in rows
            }
        except Exception as exc:
            logger.error(f"context_get_failed error={exc}")
            return {}

    def build_prompt_context(self, session_id: str, current_query: str) -> str:
        """Build a concise prompt prefix from stored session context."""
        try:
            modules = self.get_context(session_id)
            lines = ["[INTELLIGENCE CONTEXT]"]
            for module, wrapper in modules.items():
                context = wrapper.get("context", {})
                if not context:
                    continue
                summary = context.get("response_summary") or context.get("query") or str(context)[:80]
                lines.append(f"- {module}: {summary}")
            lines.append(f"[USER QUERY]\n{current_query}")
            return "\n".join(lines)
        except Exception as exc:
            logger.error(f"build_prompt_context_failed error={exc}")
            return f"[USER QUERY]\n{current_query}"

    def get_entity_aware_context(
        self,
        session_id: str,
        entity_type: str,
        entity_id: str,
        entity_graph: "EntityGraph",
    ) -> str:
        """Build context for a specific entity using graph relationships."""
        try:
            entity = entity_graph.get_entity(entity_type, entity_id)
            related = entity_graph.get_related(entity_type, entity_id)
            history = entity_graph.get_entity_timeline(entity_type, entity_id, limit=10)

            lines = [f"[ENTITY CONTEXT: {entity_type.upper()} {entity_id}]"]
            if entity:
                lines.append(f"Name: {entity.get('name', entity_id)}")
                lines.append(f"Data: {entity.get('data', {})}")

            if related:
                lines.append("Related entities:")
                for rel in related[:10]:
                    lines.append(
                        f"- {rel.get('relationship')} -> {rel.get('type')}:{rel.get('id')} "
                        f"({rel.get('name', 'unknown')}, strength {rel.get('strength_score', 1.0)})"
                    )

            if history:
                lines.append("Recent events:")
                for event in history[:10]:
                    lines.append(f"- {event.get('timestamp')} {event.get('type')} ({event.get('priority')})")

            return "\n".join(lines)
        except Exception as exc:
            logger.error(f"entity_aware_context_failed error={exc}")
            return f"[ENTITY CONTEXT: {entity_type.upper()} {entity_id}]"

    def clear_session(self, session_id: str) -> bool:
        """Remove all stored context for a session."""
        try:
            self._pool.execute(
                "DELETE FROM context_sessions WHERE session_id = ?",
                (session_id,),
            )
            logger.info(f"context_session_cleared session_id={session_id}")
            return True
        except Exception as exc:
            logger.error(f"context_clear_failed error={exc}")
            return False
