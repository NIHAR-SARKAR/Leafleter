"""Entity graph for the Intelligence Core.

Stores typed entities and typed relationships between them, enabling
multi-hop exploration of competitors, topics, alerts, searches, and actions.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from .database import SQLiteConnectionPool, deserialize_json, serialize_json

logger = logging.getLogger(__name__)


class EntityGraph:
    """Graph storage for intelligence entities and relationships."""

    def __init__(self, db_path: str = "data/intelligence.db") -> None:
        self.db_path = db_path
        self._pool = SQLiteConnectionPool(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Database is initialized by :class:`SQLiteConnectionPool`."""
        logger.info(f"entity_graph_ready db_path={self.db_path}")

    def add_entity(self, entity_type: str, entity_id: str, name: str, data: dict) -> bool:
        """Add or replace an entity in the graph."""
        try:
            now = datetime.utcnow().isoformat()
            self._pool.execute(
                """
                INSERT INTO entities (id, type, name, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    type = excluded.type,
                    name = excluded.name,
                    data_json = excluded.data_json,
                    updated_at = excluded.updated_at
                """,
                (entity_id, entity_type, name, serialize_json(data), now, now),
            )
            logger.info(f"entity_added entity_type={entity_type} entity_id={entity_id} name={name}")
            return True
        except Exception as exc:
            logger.error(f"entity_add_failed entity_type={entity_type} entity_id={entity_id} error={exc}")
            return False

    def get_or_create(self, entity_type: str, entity_id: str, name: str, data: dict) -> dict:
        """Return an existing entity or create it if it does not exist."""
        existing = self.get_entity(entity_type, entity_id)
        if existing:
            return existing
        self.add_entity(entity_type, entity_id, name, data)
        return self.get_entity(entity_type, entity_id) or {
            "id": entity_id,
            "type": entity_type,
            "name": name,
            "data": data,
        }

    def link_entities(
        self,
        from_type: str,
        from_id: str,
        to_type: str,
        to_id: str,
        relationship: str,
        strength: float = 1.0,
    ) -> bool:
        """Create a directional relationship between two entities."""
        try:
            self._pool.execute(
                """
                INSERT INTO relationships (from_id, from_type, to_id, to_type, relationship, strength_score)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT DO NOTHING
                """,
                (from_id, from_type, to_id, to_type, relationship, strength),
            )
            logger.info(
                "entity_linked from_type=%s from_id=%s to_type=%s to_id=%s relationship=%s",
                from_type, from_id, to_type, to_id, relationship,
            )
            return True
        except Exception as exc:
            logger.error(f"entity_link_failed error={exc}")
            return False

    def get_related(
        self,
        entity_type: str,
        entity_id: str,
        relationship_filter: str | None = None,
    ) -> list[dict]:
        """Return entities related to ``entity_id`` along with relationship metadata."""
        if relationship_filter:
            rows = self._pool.fetchall(
                """
                SELECT r.relationship, r.strength_score, r.to_type AS type, r.to_id AS id, e.name, e.data_json
                FROM relationships r
                LEFT JOIN entities e ON e.type = r.to_type AND e.id = r.to_id
                WHERE r.from_type = ? AND r.from_id = ? AND r.relationship = ?
                ORDER BY r.strength_score DESC, r.created_at DESC
                """,
                (entity_type, entity_id, relationship_filter),
            )
        else:
            rows = self._pool.fetchall(
                """
                SELECT r.relationship, r.strength_score, r.to_type AS type, r.to_id AS id, e.name, e.data_json
                FROM relationships r
                LEFT JOIN entities e ON e.type = r.to_type AND e.id = r.to_id
                WHERE r.from_type = ? AND r.from_id = ?
                ORDER BY r.strength_score DESC, r.created_at DESC
                """,
                (entity_type, entity_id),
            )
        return [
            {
                "relationship": row["relationship"],
                "strength_score": row["strength_score"],
                "type": row["type"],
                "id": row["id"],
                "name": row["name"] or row["id"],
                "data": deserialize_json(row["data_json"], {}),
            }
            for row in rows
        ]

    def find_by_keyword(self, keyword: str) -> list[dict]:
        """Search entities by keyword across id, name, or JSON data."""
        pattern = f"%{keyword}%"
        rows = self._pool.fetchall(
            """
            SELECT id, type, name, data_json, created_at, updated_at
            FROM entities
            WHERE id LIKE ? OR name LIKE ? OR data_json LIKE ?
            ORDER BY updated_at DESC
            """,
            (pattern, pattern, pattern),
        )
        return [self._row_to_entity(row) for row in rows]

    def get_entity(self, entity_type: str, entity_id: str) -> dict | None:
        """Return a single entity by type and id."""
        row = self._pool.fetchone(
            """
            SELECT id, type, name, data_json, created_at, updated_at
            FROM entities
            WHERE type = ? AND id = ?
            """,
            (entity_type, entity_id),
        )
        return self._row_to_entity(row) if row else None

    def get_entity_timeline(self, entity_type: str, entity_id: str, limit: int = 50) -> list[dict]:
        """Return recent events that mention this entity in their payload."""
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
        return [
            {
                "id": row["id"],
                "type": row["type"],
                "source": row["source"],
                "payload": deserialize_json(row["payload_json"], {}),
                "priority": row["priority"],
                "processed": bool(row["processed"]),
                "timestamp": row["created_at"],
            }
            for row in rows
        ]

    def update_entity_data(self, entity_type: str, entity_id: str, data_updates: dict) -> bool:
        """Merge ``data_updates`` into the entity's existing data blob."""
        try:
            existing = self.get_entity(entity_type, entity_id)
            if not existing:
                logger.warning(f"entity_update_missing entity_type={entity_type} entity_id={entity_id}")
                return False
            merged = {**existing.get("data", {}), **data_updates}
            now = datetime.utcnow().isoformat()
            self._pool.execute(
                """
                UPDATE entities
                SET data_json = ?, updated_at = ?
                WHERE type = ? AND id = ?
                """,
                (serialize_json(merged), now, entity_type, entity_id),
            )
            logger.info(f"entity_updated entity_type={entity_type} entity_id={entity_id}")
            return True
        except Exception as exc:
            logger.error(f"entity_update_failed error={exc}")
            return False

    def count_entities(self, entity_type: str | None = None) -> int:
        """Return the total number of entities, optionally filtered by type."""
        if entity_type:
            row = self._pool.fetchone(
                "SELECT COUNT(*) AS count FROM entities WHERE type = ?",
                (entity_type,),
            )
        else:
            row = self._pool.fetchone("SELECT COUNT(*) AS count FROM entities")
        return row["count"] if row else 0

    def health_check(self) -> dict:
        """Return a simple health status for the entity graph."""
        try:
            entity_count = self.count_entities()
            return {"status": "ok", "entities": entity_count}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def _row_to_entity(self, row: dict) -> dict:
        return {
            "id": row["id"],
            "type": row["type"],
            "name": row["name"],
            "data": deserialize_json(row["data_json"], {}),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
