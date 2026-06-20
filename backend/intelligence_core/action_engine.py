"""Action engine for the Intelligence Core.

Turns events and insights into scored, actionable recommendations.  Actions
are persisted so they can be reviewed, executed, or dismissed from the UI.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from .database import SQLiteConnectionPool, deserialize_json, serialize_json

logger = logging.getLogger(__name__)


class ActionEngine:
    """Generate and manage recommended actions across modules."""

    ACTION_TYPES = [
        "generate_content_brief",
        "update_battlecard",
        "schedule_social",
        "adjust_ppc",
        "notify_team",
        "create_report",
        "monitor_closely",
        "competitive_response",
    ]

    def __init__(self, db_path: str = "data/intelligence.db", ai_provider: Any = None) -> None:
        self.db_path = db_path
        self._pool = SQLiteConnectionPool(db_path)
        self.ai_provider = ai_provider

    def generate_actions(self, event_or_insight: dict) -> list[dict]:
        """Generate actions for an event or insight and persist them."""
        actions: list[dict] = []
        event_type = event_or_insight.get("type", "")
        payload = event_or_insight.get("payload", {})

        # Rule-based action generation for known event types.
        if event_type == "competitor.added":
            actions.append(self._build_action(
                action_type="update_battlecard",
                entity_type="competitor",
                entity_id=payload.get("competitor_id"),
                title=f"Create battlecard for {payload.get('name', 'new competitor')}",
                description=f"A new competitor ({payload.get('name')}) was added. Prepare a battlecard.",
                why_matters="Understanding new competitors early prevents market-share surprises.",
                expected_outcome="Sales and marketing have a ready-to-use competitive positioning doc.",
                source_modules=["competitor"],
                urgency=6,
                effort=4,
                impact_score=7,
            ))
            actions.append(self._build_action(
                action_type="monitor_closely",
                entity_type="competitor",
                entity_id=payload.get("competitor_id"),
                title=f"Monitor {payload.get('name', 'competitor')}",
                description="Track mentions, pricing, and product changes for this competitor.",
                why_matters="Early detection of competitive moves enables faster response.",
                expected_outcome="Regular alerts when this competitor makes notable changes.",
                source_modules=["competitor", "search"],
                urgency=5,
                effort=2,
                impact_score=6,
            ))

        elif event_type == "competitor.updated" and payload.get("significant"):
            actions.append(self._build_action(
                action_type="competitive_response",
                entity_type="competitor",
                entity_id=payload.get("competitor_id"),
                title=f"Respond to {payload.get('competitor_name', 'competitor')} update",
                description="A significant competitor change was detected.",
                why_matters="Significant competitive changes can shift buyer preference quickly.",
                expected_outcome="Aligned response messaging across sales and marketing.",
                source_modules=["competitor", "alerts"],
                urgency=8,
                effort=5,
                impact_score=8,
            ))

        elif event_type == "topic.anomaly_detected":
            direction = payload.get("direction", "up")
            actions.append(self._build_action(
                action_type="generate_content_brief",
                entity_type="topic",
                entity_id=payload.get("topic_id"),
                title=f"Content brief for trending topic {payload.get('topic_id')}",
                description=f"Topic volume is trending {direction} by {payload.get('change_pct', 0):.1f}%.",
                why_matters="Trending topics are content opportunities before competitors saturate them.",
                expected_outcome="Publish-ready content brief that captures search demand.",
                source_modules=["topics"],
                urgency=7 if direction == "up" else 5,
                effort=3,
                impact_score=8,
            ))
            actions.append(self._build_action(
                action_type="schedule_social",
                entity_type="topic",
                entity_id=payload.get("topic_id"),
                title="Schedule social posts on trending topic",
                description="Amplify owned content while the topic is hot.",
                why_matters="Social velocity compounds organic reach for trending topics.",
                expected_outcome="Scheduled posts aligned with the topic trend.",
                source_modules=["topics"],
                urgency=7,
                effort=2,
                impact_score=6,
            ))

        elif event_type == "search.potential_competitor_detected":
            actions.append(self._build_action(
                action_type="monitor_closely",
                entity_type="company",
                entity_id=payload.get("company_name", "").lower().replace(" ", "_"),
                title=f"Monitor potential competitor {payload.get('company_name')}",
                description=f"Detected {payload.get('mention_count', 0)} mentions in search.",
                why_matters="New entrants often first appear as repeated search mentions.",
                expected_outcome="Decision on whether to add to official competitor watchlist.",
                source_modules=["search"],
                urgency=5,
                effort=2,
                impact_score=6,
            ))

        elif event_type == "alert.created":
            actions.append(self._build_action(
                action_type="notify_team",
                entity_type="alert",
                entity_id=payload.get("alert_id"),
                title=f"Review alert: {payload.get('title', 'New alert')}",
                description=payload.get("description", ""),
                why_matters="Alerts require human review to decide on response.",
                expected_outcome="Team acknowledges and triages the alert.",
                source_modules=["alerts"],
                urgency=payload.get("urgency", 5),
                effort=1,
                impact_score=5,
            ))

        # Optional AI-generated actions for richer recommendations.
        if self.ai_provider and len(actions) < 3:
            try:
                ai_actions = self._generate_ai_actions(event_or_insight)
                actions.extend(ai_actions)
            except Exception as exc:
                logger.warning(f"ai_action_generation_failed error={exc}")

        # Persist and score every generated action.
        scored = []
        for action in actions:
            action = self.score_action(action)
            self._persist_action(action)
            scored.append(action)
        return scored

    def score_action(self, action: dict) -> dict:
        """Score an action by urgency, effort, and impact."""
        urgency = int(action.get("urgency", 5))
        effort = int(action.get("effort", 5))
        impact = int(action.get("impact_score", 5))
        priority_score = round((urgency * impact) / max(effort, 1), 2)
        action["priority_score"] = priority_score
        return action

    def get_actions_for_entity(
        self,
        entity_type: str,
        entity_id: str,
        status: str = "pending",
    ) -> list[dict]:
        """Return actions for a specific entity."""
        rows = self._pool.fetchall(
            """
            SELECT * FROM actions
            WHERE entity_type = ? AND entity_id = ? AND status = ?
            ORDER BY priority_score DESC, urgency DESC, created_at DESC
            """,
            (entity_type, entity_id, status),
        )
        return [self._row_to_action(row) for row in rows]

    def get_priority_queue(self, limit: int = 10) -> list[dict]:
        """Return the top-scoring pending actions."""
        rows = self._pool.fetchall(
            """
            SELECT * FROM actions
            WHERE status = 'pending'
            ORDER BY priority_score DESC, urgency DESC, created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [self._row_to_action(row) for row in rows]

    def get_action(self, action_id: str) -> dict | None:
        """Return a single action by id."""
        row = self._pool.fetchone(
            "SELECT * FROM actions WHERE id = ?",
            (action_id,),
        )
        return self._row_to_action(row) if row else None

    def mark_action_executed(self, action_id: str, result: dict) -> bool:
        """Mark an action as executed and store the result."""
        try:
            now = datetime.utcnow().isoformat()
            action = self.get_action(action_id)
            if not action:
                return False
            result_blob = {**(action.get("result") or {}), **result, "executed_at": now}
            self._pool.execute(
                """
                UPDATE actions
                SET status = 'executed', executed_at = ?, result_json = ?
                WHERE id = ?
                """,
                (now, serialize_json(result_blob), action_id),
            )
            logger.info(f"action_executed action_id={action_id}")
            return True
        except Exception as exc:
            logger.error(f"action_execute_failed error={exc}")
            return False

    def dismiss_action(self, action_id: str, reason: str) -> bool:
        """Dismiss an action without executing it."""
        try:
            now = datetime.utcnow().isoformat()
            self._pool.execute(
                """
                UPDATE actions
                SET status = 'dismissed', executed_at = ?, result_json = ?
                WHERE id = ?
                """,
                (now, serialize_json({"dismissed_at": now, "reason": reason}), action_id),
            )
            logger.info(f"action_dismissed action_id={action_id} reason={reason}")
            return True
        except Exception as exc:
            logger.error(f"action_dismiss_failed error={exc}")
            return False

    def _build_ai_prompt(self, event: dict) -> str:
        """Build a prompt for AI action generation."""
        return (
            "You are a marketing intelligence assistant. Given the following event, "
            "suggest up to 3 concrete actions a marketing team should take. "
            "Return JSON with fields: type (one of the allowed action types), title, "
            "description, why_matters, expected_outcome, urgency (1-10), effort (1-10), "
            "impact_score (1-10).\n\n"
            f"Event: {json.dumps(event, default=str)}"
        )

    def _generate_ai_actions(self, event_or_insight: dict) -> list[dict]:
        """Ask the AI provider for additional actions."""
        if not self.ai_provider:
            return []
        prompt = self._build_ai_prompt(event_or_insight)
        try:
            response = self.ai_provider.generate_response(prompt)
            parsed = json.loads(response)
            ai_actions = parsed if isinstance(parsed, list) else [parsed]
            valid = []
            for action in ai_actions:
                if action.get("type") in self.ACTION_TYPES:
                    valid.append(action)
            return valid
        except Exception as exc:
            logger.warning(f"ai_action_parse_failed error={exc}")
            return []

    def _build_action(
        self,
        action_type: str,
        entity_type: str,
        entity_id: str,
        title: str,
        description: str,
        why_matters: str,
        expected_outcome: str,
        source_modules: list[str],
        urgency: int = 5,
        effort: int = 5,
        impact_score: int = 5,
        related_entities: list[dict] | None = None,
    ) -> dict:
        action_id = f"act_{uuid.uuid4().hex[:12]}"
        return {
            "id": action_id,
            "type": action_type,
            "entity_type": entity_type,
            "entity_id": entity_id or action_id,
            "title": title,
            "description": description,
            "why_matters": why_matters,
            "expected_outcome": expected_outcome,
            "source_modules": source_modules,
            "related_entities": related_entities or [],
            "urgency": urgency,
            "effort": effort,
            "impact_score": impact_score,
            "status": "pending",
        }

    def _persist_action(self, action: dict) -> None:
        self._pool.execute(
            """
            INSERT INTO actions (
                id, type, entity_id, entity_type, title, description,
                why_matters, expected_outcome, source_modules_json,
                related_entities_json, urgency, effort, impact_score, priority_score, status,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status = excluded.status,
                urgency = excluded.urgency,
                effort = excluded.effort,
                impact_score = excluded.impact_score,
                priority_score = excluded.priority_score
            """,
            (
                action["id"],
                action["type"],
                action["entity_id"],
                action["entity_type"],
                action["title"],
                action["description"],
                action["why_matters"],
                action["expected_outcome"],
                serialize_json(action["source_modules"]),
                serialize_json(action["related_entities"]),
                action["urgency"],
                action["effort"],
                action["impact_score"],
                action["priority_score"],
                action["status"],
                datetime.utcnow().isoformat(),
            ),
        )

    def _row_to_action(self, row: dict) -> dict:
        return {
            "id": row["id"],
            "type": row["type"],
            "entity_id": row["entity_id"],
            "entity_type": row["entity_type"],
            "title": row["title"],
            "description": row["description"],
            "why_matters": row["why_matters"],
            "expected_outcome": row["expected_outcome"],
            "source_modules": deserialize_json(row["source_modules_json"], []),
            "related_entities": deserialize_json(row["related_entities_json"], []),
            "urgency": row["urgency"],
            "effort": row["effort"],
            "impact_score": row["impact_score"],
            "priority_score": row.get("priority_score")
                or round((row["urgency"] * row["impact_score"]) / max(row["effort"], 1), 2),
            "status": row["status"],
            "created_at": row["created_at"],
            "executed_at": row["executed_at"],
        }
