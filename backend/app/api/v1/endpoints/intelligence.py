"""Unified Intelligence API endpoints."""

from __future__ import annotations

import asyncio
import contextlib
from typing import Annotated, Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.deps import ActiveUserDep, DbDep, OrgIdDep
from app.core.exceptions import NotFoundException
from app.core.intelligence import get_intelligence_core
from app.core.logging import get_logger
from app.models.organization import Organization
from app.schemas.rag import AskRequest

logger = get_logger(__name__)
router = APIRouter(tags=["intelligence"])


def _core() -> dict[str, Any]:
    return get_intelligence_core()


def _to_thread(func: Any, *args: Any, **kwargs: Any) -> Any:
    """Run a synchronous intelligence core function in the default executor."""
    return asyncio.to_thread(func, *args, **kwargs)


@router.get("/today")
async def get_today_intelligence(
    core: Annotated[dict[str, Any], Depends(_core)],
) -> dict[str, Any]:
    """Return today's intelligence snapshot for the dashboard."""
    if not core or not settings.ENABLE_INTELLIGENCE_CORE:
        return {"enabled": False, "message": "Intelligence core is disabled"}

    try:
        priority_queue = await _to_thread(core["action_engine"].get_priority_queue, 20)
        recent_events = await _to_thread(core["event_bus"].get_recent_events, 24)
        workflows = await _to_thread(core["workflow_engine"].get_active_workflows)
        alerts = [e for e in recent_events if e.get("type", "").startswith("alert.")]
        opportunities = [e for e in recent_events if e.get("type", "") == "topic.anomaly_detected"]
        threats = [e for e in recent_events if e.get("type", "") == "competitor.updated"]

        return {
            "enabled": True,
            "alerts": {"count": len(alerts), "new": len(alerts)},
            "opportunities": {
                "count": len(opportunities),
                "urgent": len([o for o in opportunities if o.get("priority") == "high"]),
            },
            "threats": {"count": len(threats), "entities": threats[:5]},
            "workflows": {"active": len(workflows)},
            "priority_queue": priority_queue,
            "recent_events": recent_events[:10],
        }
    except Exception as exc:
        logger.error("today_intelligence_failed", error=str(exc))
        return {"enabled": True, "error": str(exc)}


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_intelligence(
    entity_type: str,
    entity_id: str,
    core: Annotated[dict[str, Any], Depends(_core)],
) -> dict[str, Any]:
    """Return full intelligence for a specific entity."""
    if not core or not settings.ENABLE_INTELLIGENCE_CORE:
        return {"enabled": False}

    try:
        entity = await _to_thread(core["entity_graph"].get_entity, entity_type, entity_id)
        related = await _to_thread(core["entity_graph"].get_related, entity_type, entity_id)
        timeline = await _to_thread(core["entity_graph"].get_entity_timeline, entity_type, entity_id, 50)
        actions = await _to_thread(
            core["action_engine"].get_actions_for_entity, entity_type, entity_id, "pending"
        )
        return {
            "entity": entity,
            "related_entities": related,
            "timeline": timeline,
            "recommended_actions": actions,
        }
    except Exception as exc:
        logger.error("entity_intelligence_failed", error=str(exc))
        return {"error": str(exc)}


@router.get("/brief/{brief_type}")
async def get_brief(
    brief_type: str,
    core: Annotated[dict[str, Any], Depends(_core)],
) -> dict[str, Any]:
    """Return a generated intelligence brief."""
    if not core or not settings.ENABLE_INTELLIGENCE_CORE:
        return {"enabled": False}

    try:
        recent_events = await _to_thread(core["event_bus"].get_recent_events, 24)
        priority_queue = await _to_thread(core["action_engine"].get_priority_queue, 10)

        if brief_type == "daily":
            title = "Daily Intelligence Pulse"
        elif brief_type == "competitor":
            title = "Competitive Brief"
        elif brief_type == "opportunity":
            title = "Opportunity Radar"
        elif brief_type == "crisis":
            title = "Crisis Brief"
        else:
            return {"error": f"Unknown brief type: {brief_type}"}

        return {
            "brief_type": brief_type,
            "title": title,
            "generated_at": __import__("datetime").datetime.utcnow().isoformat(),
            "executive_summary": f"{title} based on {len(recent_events)} recent events and {len(priority_queue)} pending actions.",
            "timeline": recent_events[:20],
            "recommended_actions": priority_queue,
            "impact_score": min(100, len(priority_queue) * 10 + len(recent_events)),
            "data_sources": list({e.get("source") for e in recent_events if e.get("source")}),
        }
    except Exception as exc:
        logger.error("brief_generation_failed", error=str(exc))
        return {"error": str(exc)}


@router.post("/action")
async def create_action(
    action_request: dict[str, Any],
    core: Annotated[dict[str, Any], Depends(_core)],
) -> dict[str, Any]:
    """Create a new action from a request payload."""
    if not core or not settings.ENABLE_INTELLIGENCE_CORE:
        return {"enabled": False}

    try:
        actions = await _to_thread(core["action_engine"].generate_actions, action_request)
        return {"actions": actions}
    except Exception as exc:
        logger.error("action_creation_failed", error=str(exc))
        return {"error": str(exc)}


@router.get("/actions")
async def list_actions(
    core: Annotated[dict[str, Any], Depends(_core)],
    status: str | None = "pending",
    limit: int = 50,
) -> dict[str, Any]:
    """List actions, optionally filtered by status."""
    if not core or not settings.ENABLE_INTELLIGENCE_CORE:
        return {"enabled": False}

    try:
        if status == "pending":
            actions = await _to_thread(core["action_engine"].get_priority_queue, limit)
        else:
            # Generic status query is not exposed directly; return priority queue as fallback.
            actions = await _to_thread(core["action_engine"].get_priority_queue, limit)
        return {"status": status, "actions": actions}
    except Exception as exc:
        logger.error("list_actions_failed", error=str(exc))
        return {"error": str(exc)}


@router.post("/actions/{action_id}/execute")
async def mark_action_executed(
    action_id: str,
    result: dict[str, Any],
    core: Annotated[dict[str, Any], Depends(_core)],
) -> dict[str, Any]:
    """Mark an action as executed with an optional result payload."""
    if not core or not settings.ENABLE_INTELLIGENCE_CORE:
        return {"enabled": False}

    try:
        success = await _to_thread(core["action_engine"].mark_action_executed, action_id, result)
        return {"success": success}
    except Exception as exc:
        logger.error("execute_action_failed", error=str(exc))
        return {"success": False, "error": str(exc)}


@router.post("/actions/{action_id}/dismiss")
async def dismiss_action(
    action_id: str,
    reason: dict[str, Any],
    core: Annotated[dict[str, Any], Depends(_core)],
) -> dict[str, Any]:
    """Dismiss an action without executing it."""
    if not core or not settings.ENABLE_INTELLIGENCE_CORE:
        return {"enabled": False}

    try:
        dismissal_reason = reason.get("reason", "dismissed_by_user")
        success = await _to_thread(core["action_engine"].dismiss_action, action_id, dismissal_reason)
        return {"success": success}
    except Exception as exc:
        logger.error("dismiss_action_failed", error=str(exc))
        return {"success": False, "error": str(exc)}


@router.get("/workflows")
async def list_workflows(
    core: Annotated[dict[str, Any], Depends(_core)],
    status: str | None = None,
) -> dict[str, Any]:
    """List workflow runs."""
    if not core or not settings.ENABLE_INTELLIGENCE_CORE:
        return {"enabled": False}

    try:
        history = await _to_thread(core["workflow_engine"].get_workflow_history, 50)
        if status:
            history = [w for w in history if w.get("status") == status]
        active = await _to_thread(core["workflow_engine"].get_active_workflows)
        return {"active": active, "history": history}
    except Exception as exc:
        logger.error("list_workflows_failed", error=str(exc))
        return {"error": str(exc)}


@router.get("/search")
async def unified_search(
    q: str,
    core: Annotated[dict[str, Any], Depends(_core)],
) -> dict[str, Any]:
    """Search the intelligence graph for entities matching ``q``."""
    if not core or not settings.ENABLE_INTELLIGENCE_CORE:
        return {"enabled": False}

    try:
        entities = await _to_thread(core["entity_graph"].find_by_keyword, q)
        events = await _to_thread(core["event_bus"].get_recent_events, 168)
        event_matches = [e for e in events if q.lower() in str(e.get("payload", "")).lower()]
        return {"query": q, "entities": entities, "events": event_matches[:20]}
    except Exception as exc:
        logger.error("unified_search_failed", error=str(exc))
        return {"error": str(exc)}


@router.post("/ask")
async def ask_Comrade(
    db: DbDep,
    org_id: OrgIdDep,
    request: AskRequest,
    current_user: ActiveUserDep,
) -> dict[str, Any]:
    """Answer a question using RAG over verified intelligence."""
    from app.services.rag_service import rag_service

    organization = await db.get(Organization, org_id)
    if organization is None:
        raise NotFoundException("Organization not found")

    response = await rag_service.ask(
        db,
        organization=organization,
        request=request,
    )
    return response.model_dump()


@router.websocket("/ws")
async def intelligence_websocket(
    websocket: WebSocket,
    core: Annotated[dict[str, Any], Depends(_core)],
) -> None:
    """Stream intelligence events to connected clients via WebSocket."""
    await websocket.accept()
    if not core or not settings.ENABLE_INTELLIGENCE_CORE:
        await websocket.send_json({"type": "status", "enabled": False})
        await websocket.close()
        return

    try:
        while True:
            # Simple polling loop: push recent events every 2 seconds.
            events = await _to_thread(core["event_bus"].get_recent_events, 1)
            if events:
                await websocket.send_json(events[-1])
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logger.info("intelligence_websocket_disconnected")
    except Exception as exc:
        logger.error("intelligence_websocket_error", error=str(exc))
    finally:
        with contextlib.suppress(Exception):
            await websocket.close()
