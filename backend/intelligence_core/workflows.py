"""Workflow engine for the Intelligence Core.

Workflows react to events published on the event bus, perform multi-step
intelligence tasks, and store their results for inspection.
"""

from __future__ import annotations

import json
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .action_engine import ActionEngine
    from .entity_graph import EntityGraph
    from .event_bus import EventBus

logger = logging.getLogger(__name__)


class Workflow(ABC):
    """Base class for intelligence workflows."""

    def __init__(self) -> None:
        self.context: dict[str, Any] = {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique workflow name."""
        pass

    @abstractmethod
    def condition(self, event: dict) -> bool:
        """Return True if this workflow should run for ``event``."""
        pass

    @abstractmethod
    def execute(self, event: dict) -> dict:
        """Execute the workflow and return a result dictionary."""
        pass

    def on_complete(self, result: dict) -> None:
        """Hook called after a workflow finishes successfully."""
        logger.info(
            "workflow_completed workflow=%s event_id=%s",
            result.get("workflow"), result.get("event_id"),
        )


class CompetitorDiscoveryWorkflow(Workflow):
    """React to potential competitor detections and add them to the graph."""

    @property
    def name(self):
        return "competitor_discovery"

    def condition(self, event):
        return event["type"] == "search.potential_competitor_detected"

    def execute(self, event):
        payload = event["payload"]
        company_name = payload.get("company_name", "")
        entity_id = company_name.lower().replace(" ", "_")

        result = {
            "workflow": self.name,
            "event_id": event["id"],
            "entity_id": entity_id,
            "entity_type": "company",
            "name": company_name,
            "actions_taken": [],
        }

        if self.context.get("entity_graph"):
            self.context["entity_graph"].add_entity(
                "company",
                entity_id,
                company_name,
                {
                    "mention_count": payload.get("mention_count", 0),
                    "query": payload.get("query", ""),
                    "sample_contexts": payload.get("sample_contexts", []),
                    "status": "candidate",
                },
            )
            result["actions_taken"].append("added_company_entity")

        if self.context.get("event_bus"):
            self.context["event_bus"].publish(
                "workflow.competitor_discovery.completed",
                "workflow",
                {"company_name": company_name, "entity_id": entity_id},
            )
            result["actions_taken"].append("published_completion_event")

        return result


class TopicOpportunityWorkflow(Workflow):
    """React to topic anomalies and surface content opportunities."""

    @property
    def name(self):
        return "topic_opportunity"

    def condition(self, event):
        return event["type"] == "topic.anomaly_detected"

    def execute(self, event):
        payload = event["payload"]
        topic_id = payload.get("topic_id", "")
        result = {
            "workflow": self.name,
            "event_id": event["id"],
            "topic_id": topic_id,
            "actions_taken": [],
        }

        entity_graph = self.context.get("entity_graph")
        if entity_graph:
            entity_graph.add_entity(
                "topic_opportunity",
                f"opp_{topic_id}",
                f"Opportunity: {topic_id}",
                {
                    "direction": payload.get("direction", "up"),
                    "change_pct": payload.get("change_pct", 0),
                    "previous_volume": payload.get("previous_volume", 0),
                    "current_volume": payload.get("current_volume", 0),
                },
            )
            entity_graph.link_entities(
                "topic", topic_id, "topic_opportunity", f"opp_{topic_id}", "generated"
            )
            result["actions_taken"].append("created_opportunity_entity")

        action_engine = self.context.get("action_engine")
        if action_engine:
            action_engine.generate_actions(event)
            result["actions_taken"].append("generated_actions")

        return result


class CompetitiveThreatWorkflow(Workflow):
    """React to competitor updates and generate threat response actions."""

    @property
    def name(self):
        return "competitive_threat"

    def condition(self, event):
        return event["type"] == "competitor.updated" and event.get("payload", {}).get("significant", False)

    def execute(self, event):
        payload = event["payload"]
        competitor_id = payload.get("competitor_id", "")
        changes = payload.get("changes", {})
        result = {
            "workflow": self.name,
            "event_id": event["id"],
            "competitor_id": competitor_id,
            "changes": changes,
            "actions_taken": [],
        }

        entity_graph = self.context.get("entity_graph")
        if entity_graph:
            entity_graph.add_entity(
                "competitive_threat",
                f"threat_{competitor_id}",
                f"Threat: {competitor_id}",
                {"changes": changes, "significant": True},
            )
            entity_graph.link_entities(
                "competitor", competitor_id, "competitive_threat", f"threat_{competitor_id}", "triggered"
            )
            result["actions_taken"].append("created_threat_entity")

        action_engine = self.context.get("action_engine")
        if action_engine:
            action_engine.generate_actions(event)
            result["actions_taken"].append("generated_response_actions")

        return result


class DailyPulseWorkflow(Workflow):
    """Generate a daily intelligence pulse."""

    @property
    def name(self):
        return "daily_pulse"

    def condition(self, event):
        return event["type"] == "scheduled.daily_pulse"

    def execute(self, event):
        entity_graph = self.context.get("entity_graph")
        action_engine = self.context.get("action_engine")
        ai_provider = self.context.get("ai_provider")

        entity_count = entity_graph.count_entities() if entity_graph else 0
        pending_actions = action_engine.get_priority_queue(limit=10) if action_engine else []

        summary_parts = [
            f"Total entities tracked: {entity_count}",
            f"Pending actions: {len(pending_actions)}",
        ]
        if pending_actions:
            summary_parts.append(f"Top priority: {pending_actions[0]['title']}")

        summary = " ".join(summary_parts)

        ai_summary = None
        if ai_provider:
            try:
                ai_summary = ai_provider.generate_intelligence_brief("daily_pulse", "today")
            except Exception as exc:
                logger.warning(f"daily_pulse_ai_failed error={exc}")

        result = {
            "workflow": self.name,
            "event_id": event["id"],
            "summary": summary,
            "ai_summary": ai_summary,
            "pending_actions_count": len(pending_actions),
        }
        return result


class SearchToTopicWorkflow(Workflow):
    """Convert search results into topic candidates and link them."""

    @property
    def name(self):
        return "search_to_topic"

    def condition(self, event):
        return event["type"] == "search.executed"

    def execute(self, event):
        payload = event["payload"]
        query = payload.get("query", "")
        top_entities = payload.get("top_entities", [])
        result = {
            "workflow": self.name,
            "event_id": event["id"],
            "query": query,
            "topics_linked": 0,
            "competitors_linked": 0,
        }

        entity_graph = self.context.get("entity_graph")
        if not entity_graph:
            return result

        search_id = f"search_{uuid.uuid4().hex[:8]}"
        entity_graph.add_entity(
            "search",
            search_id,
            query,
            {
                "results_count": payload.get("results_count", 0),
                "top_entities": top_entities,
            },
        )

        for entity in top_entities:
            entity_type = entity.get("type")
            entity_id = entity.get("id")
            if entity_type and entity_id:
                entity_graph.get_or_create(
                    entity_type,
                    entity_id,
                    entity.get("name", entity_id),
                    entity.get("data", {}),
                )
                entity_graph.link_entities("search", search_id, entity_type, entity_id, "found_in")
                if entity_type == "topic":
                    result["topics_linked"] += 1
                elif entity_type == "competitor":
                    result["competitors_linked"] += 1

        return result


class WorkflowEngine:
    """Registers workflows and dispatches events to matching workflows."""

    def __init__(
        self,
        event_bus: "EventBus",
        entity_graph: "EntityGraph",
        action_engine: "ActionEngine",
        ai_provider: Any,
    ) -> None:
        self.event_bus = event_bus
        self.entity_graph = entity_graph
        self.action_engine = action_engine
        self.ai_provider = ai_provider
        self.workflows: list[Workflow] = []
        self.active_workflows: dict[str, dict] = {}
        self.context = {
            "entity_graph": entity_graph,
            "action_engine": action_engine,
            "ai_provider": ai_provider,
            "event_bus": event_bus,
        }
        self._subscribed = False

    def register(self, workflow: Workflow) -> None:
        """Register a workflow instance."""
        workflow.context = self.context
        self.workflows.append(workflow)
        logger.info(f"workflow_registered workflow={workflow.name}")

    def start(self) -> None:
        """Subscribe the engine to all events on the event bus."""
        if self._subscribed:
            return
        self.event_bus.subscribe_pattern(".*", self._on_event)
        self._subscribed = True
        logger.info("workflow_engine_started")

    def _on_event(self, event: dict) -> None:
        """Evaluate all workflows against an event and run matches."""
        for workflow in self.workflows:
            try:
                if workflow.condition(event):
                    workflow_id = f"{workflow.name}_{uuid.uuid4().hex[:8]}"
                    self.active_workflows[workflow_id] = {
                        "id": workflow_id,
                        "type": workflow.name,
                        "status": "running",
                        "trigger_event_id": event["id"],
                        "started_at": datetime.utcnow().isoformat(),
                    }
                    result = workflow.execute(event)
                    result["workflow_id"] = workflow_id
                    self._persist_workflow(workflow_id, workflow.name, event["id"], result)
                    workflow.on_complete(result)
                    self.active_workflows[workflow_id]["status"] = "completed"
                    self.active_workflows[workflow_id]["completed_at"] = datetime.utcnow().isoformat()
            except Exception as exc:
                logger.error(f"workflow_execution_failed workflow={workflow.name} error={exc}")

    def get_active_workflows(self) -> dict[str, Any]:
        """Return workflows that have not yet completed."""
        return {
            wid: info
            for wid, info in self.active_workflows.items()
            if info.get("status") != "completed"
        }

    def get_workflow_history(self, limit: int = 50) -> list[dict]:
        """Return persisted workflow runs ordered by most recent."""
        rows = self.event_bus._pool.fetchall(
            """
            SELECT id, type, status, trigger_event_id, result_json, created_at, completed_at
            FROM workflows
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [
            {
                "id": row["id"],
                "type": row["type"],
                "status": row["status"],
                "trigger_event_id": row["trigger_event_id"],
                "result": json.loads(row["result_json"]) if row["result_json"] else {},
                "created_at": row["created_at"],
                "completed_at": row["completed_at"],
            }
            for row in rows
        ]

    def _persist_workflow(self, workflow_id: str, workflow_type: str, trigger_event_id: str, result: dict) -> None:
        now = datetime.utcnow().isoformat()
        self.event_bus._pool.execute(
            """
            INSERT INTO workflows (id, type, status, trigger_event_id, result_json, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status = excluded.status,
                result_json = excluded.result_json,
                completed_at = excluded.completed_at
            """,
            (
                workflow_id,
                workflow_type,
                "completed",
                trigger_event_id,
                json.dumps(result, default=str),
                now,
                now,
            ),
        )
