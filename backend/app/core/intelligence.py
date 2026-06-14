"""Global Intelligence Core instances for Leafleter.

The intelligence core is intentionally decoupled from the async SQLAlchemy
application database.  This module lazily initializes singletons and wires
them into the existing service layer when enabled.
"""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_intelligence_core: dict[str, Any] = {}


def init_intelligence_core() -> dict[str, Any]:
    """Initialize and return the global intelligence core components."""
    global _intelligence_core
    if _intelligence_core:
        return _intelligence_core

    try:
        from intelligence_core import (  # type: ignore
            ActionEngine,
            ContextMemory,
            EntityGraph,
            EventBus,
            WorkflowEngine,
        )
        from intelligence_core.workflows import (  # type: ignore
            CompetitiveThreatWorkflow,
            CompetitorDiscoveryWorkflow,
            DailyPulseWorkflow,
            SearchToTopicWorkflow,
            TopicOpportunityWorkflow,
        )
    except ImportError as exc:
        logger.warning("intelligence_core_unavailable", error=str(exc))
        return {}

    db_path = settings.INTELLIGENCE_DB_PATH
    entity_graph = EntityGraph(db_path)
    event_bus = EventBus(db_path)
    context_memory = ContextMemory(db_path)
    action_engine = ActionEngine(db_path, ai_provider=None)
    workflow_engine = WorkflowEngine(event_bus, entity_graph, action_engine, ai_provider=None)

    workflow_engine.register(CompetitorDiscoveryWorkflow())
    workflow_engine.register(TopicOpportunityWorkflow())
    workflow_engine.register(CompetitiveThreatWorkflow())
    workflow_engine.register(DailyPulseWorkflow())
    workflow_engine.register(SearchToTopicWorkflow())

    if settings.ENABLE_INTELLIGENCE_CORE:
        from app.services.intelligence_hooks import init_intelligence

        init_intelligence(
            entity_graph=entity_graph,
            event_bus=event_bus,
            context_memory=context_memory,
            action_engine=action_engine,
        )

    if settings.ENABLE_AUTO_WORKFLOWS:
        workflow_engine.start()
        event_bus.start_listener()

    _intelligence_core = {
        "entity_graph": entity_graph,
        "event_bus": event_bus,
        "context_memory": context_memory,
        "action_engine": action_engine,
        "workflow_engine": workflow_engine,
    }
    logger.info("intelligence_core_initialized", enabled=settings.ENABLE_INTELLIGENCE_CORE)
    return _intelligence_core


def get_intelligence_core() -> dict[str, Any]:
    """Return the initialized intelligence core."""
    if not _intelligence_core:
        return init_intelligence_core()
    return _intelligence_core


def shutdown_intelligence_core() -> None:
    """Stop background listeners and close intelligence core resources."""
    global _intelligence_core
    if not _intelligence_core:
        return
    try:
        event_bus = _intelligence_core.get("event_bus")
        if event_bus:
            event_bus.stop_listener()
    except Exception as exc:
        logger.warning("intelligence_core_shutdown_failed", error=str(exc))
    _intelligence_core = {}
