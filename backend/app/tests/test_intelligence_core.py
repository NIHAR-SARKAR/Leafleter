"""Integration tests for the Intelligence Core."""

from __future__ import annotations

import os
import tempfile
import time
from datetime import datetime, timedelta

import pytest

from intelligence_core import ActionEngine, ContextMemory, EntityGraph, EventBus
from intelligence_core.workflows import (  # type: ignore
    CompetitorDiscoveryWorkflow,
    TopicOpportunityWorkflow,
    WorkflowEngine,
)


@pytest.fixture
def db_path():
    """Provide a temporary SQLite database path."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture
def entity_graph(db_path):
    return EntityGraph(db_path)


@pytest.fixture
def event_bus(db_path):
    return EventBus(db_path)


@pytest.fixture
def action_engine(db_path):
    return ActionEngine(db_path)


@pytest.fixture
def context_memory(db_path):
    return ContextMemory(db_path)


class TestIntelligenceCore:
    def test_entity_graph_crud(self, entity_graph):
        """Entities can be created, retrieved, updated, and related."""
        assert entity_graph.add_entity("competitor", "comp_1", "Acme", {"domain": "acme.com"})
        entity = entity_graph.get_entity("competitor", "comp_1")
        assert entity is not None
        assert entity["name"] == "Acme"
        assert entity["data"]["domain"] == "acme.com"

        assert entity_graph.update_entity_data("competitor", "comp_1", {"industry": "widgets"})
        entity = entity_graph.get_entity("competitor", "comp_1")
        assert entity["data"]["industry"] == "widgets"
        assert entity["data"]["domain"] == "acme.com"

        assert entity_graph.add_entity("topic", "topic_1", "Widget Trends", {"volume": 100})
        assert entity_graph.link_entities("competitor", "comp_1", "topic", "topic_1", "interested_in")
        related = entity_graph.get_related("competitor", "comp_1")
        assert len(related) == 1
        assert related[0]["relationship"] == "interested_in"

    def test_event_bus_publish_subscribe(self, event_bus):
        """Events are persisted and delivered to subscribers."""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe("test.event", handler)
        event_bus.start_listener()

        event_id = event_bus.publish("test.event", "test", {"hello": "world"})
        time.sleep(0.2)

        assert len(received) == 1
        assert received[0]["id"] == event_id
        assert received[0]["payload"]["hello"] == "world"

        event_bus.stop_listener()

    def test_workflow_trigger(self, db_path):
        """A workflow runs when its condition matches a published event."""
        entity_graph = EntityGraph(db_path)
        event_bus = EventBus(db_path)
        action_engine = ActionEngine(db_path)
        workflow_engine = WorkflowEngine(event_bus, entity_graph, action_engine, ai_provider=None)
        workflow_engine.register(CompetitorDiscoveryWorkflow())
        workflow_engine.start()
        event_bus.start_listener()

        event_bus.publish(
            "search.potential_competitor_detected",
            "search",
            {"company_name": "NewCo", "mention_count": 3, "query": "widgets", "sample_contexts": []},
        )
        time.sleep(0.5)

        entity = entity_graph.get_entity("company", "newco")
        assert entity is not None
        assert entity["name"] == "NewCo"

        event_bus.stop_listener()

    def test_full_intelligence_flow(self, db_path):
        """A competitor update triggers workflow, alert entity, and actions."""
        entity_graph = EntityGraph(db_path)
        event_bus = EventBus(db_path)
        action_engine = ActionEngine(db_path)
        workflow_engine = WorkflowEngine(event_bus, entity_graph, action_engine, ai_provider=None)
        workflow_engine.register(TopicOpportunityWorkflow())
        workflow_engine.start()
        event_bus.start_listener()

        entity_graph.add_entity("topic", "topic_1", "AI Trends", {"volume": 100})
        event_bus.publish(
            "topic.anomaly_detected",
            "topics",
            {
                "topic_id": "topic_1",
                "topic_name": "AI Trends",
                "direction": "up",
                "change_pct": 60,
                "previous_volume": 100,
                "current_volume": 160,
            },
            priority="high",
        )
        time.sleep(0.5)

        actions = action_engine.get_actions_for_entity("topic", "topic_1")
        assert len(actions) > 0

        opportunity = entity_graph.get_entity("topic_opportunity", "opp_topic_1")
        assert opportunity is not None

        event_bus.stop_listener()

    def test_module_fallback(self, db_path):
        """A broken subscriber does not break subsequent operations."""
        event_bus = EventBus(db_path)
        event_bus.start_listener()

        def bad_handler(event):
            raise RuntimeError("boom")

        def good_handler(event):
            pass

        event_bus.subscribe("fallback.event", bad_handler)
        event_bus.subscribe("fallback.event", good_handler)

        # Should not raise.
        event_bus.publish("fallback.event", "test", {"ok": True})
        time.sleep(0.2)

        event_bus.stop_listener()

    def test_entity_aware_ai_prompt(self, db_path, context_memory):
        """Context memory builds entity-aware prompt context."""
        entity_graph = EntityGraph(db_path)
        entity_graph.add_entity("competitor", "comp_1", "Acme", {"domain": "acme.com"})
        entity_graph.link_entities("competitor", "comp_1", "topic", "topic_1", "interested_in")
        entity_graph.add_entity("topic", "topic_1", "Widgets", {"volume": 50})

        context = context_memory.get_entity_aware_context("session_1", "competitor", "comp_1", entity_graph)
        assert "Acme" in context
        assert "Widgets" in context

    def test_recent_events_filter(self, event_bus):
        """Recent events can be filtered by source and type."""
        event_bus.publish("search.executed", "search", {"query": "a"})
        event_bus.publish("search.executed", "search", {"query": "b"})
        event_bus.publish("competitor.added", "competitor", {"name": "Acme"})

        search_events = event_bus.get_recent_events(hours=24, event_type="search.executed")
        assert len(search_events) == 2

        competitor_events = event_bus.get_recent_events(hours=24, source="competitor")
        assert len(competitor_events) == 1

    def test_priority_queue(self, action_engine):
        """Actions are scored and returned in priority order."""
        action_engine.generate_actions(
            {
                "type": "topic.anomaly_detected",
                "payload": {
                    "topic_id": "t1",
                    "topic_name": "Trend",
                    "direction": "up",
                    "change_pct": 80,
                    "previous_volume": 10,
                    "current_volume": 18,
                },
            }
        )
        queue = action_engine.get_priority_queue(limit=10)
        assert len(queue) > 0
        assert all("priority_score" in a for a in queue)
        scores = [a["priority_score"] for a in queue]
        assert scores == sorted(scores, reverse=True)

    def test_action_execute_and_dismiss(self, action_engine):
        """Actions can be executed and dismissed."""
        actions = action_engine.generate_actions(
            {
                "type": "alert.created",
                "payload": {"alert_id": "alert_1", "title": "Test alert", "urgency": 5},
            }
        )
        assert len(actions) > 0
        action_id = actions[0]["id"]

        assert action_engine.mark_action_executed(action_id, {"outcome": "done"})
        executed = action_engine.get_action(action_id)
        assert executed["status"] == "executed"

        actions = action_engine.generate_actions(
            {
                "type": "alert.created",
                "payload": {"alert_id": "alert_2", "title": "Test alert 2", "urgency": 3},
            }
        )
        action_id = actions[0]["id"]
        assert action_engine.dismiss_action(action_id, "not_relevant")
        dismissed = action_engine.get_action(action_id)
        assert dismissed["status"] == "dismissed"
