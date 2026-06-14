"""Integration hooks between Leafleter modules and the Intelligence Core.

This module is the only place that imports from ``intelligence_core`` on
behalf of the existing services.  All hooks are optional and wrapped in
broad exception handling so that a failure in the intelligence layer never
breaks the core application.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    from intelligence_core import (  # type: ignore
        ActionEngine,
        ContextMemory,
        EntityGraph,
        EventBus,
    )

    _INTELLIGENCE_AVAILABLE = True
except ImportError:
    _INTELLIGENCE_AVAILABLE = False

# Global intelligence core instances.  Populated by ``init_intelligence``.
_entity_graph: EntityGraph | None = None  # type: ignore
_event_bus: EventBus | None = None  # type: ignore
_context_memory: ContextMemory | None = None  # type: ignore
_action_engine: ActionEngine | None = None  # type: ignore


def init_intelligence(
    entity_graph: Any = None,
    event_bus: Any = None,
    context_memory: Any = None,
    action_engine: Any = None,
) -> None:
    """Initialize module hooks with shared intelligence core instances."""
    global _entity_graph, _event_bus, _context_memory, _action_engine
    _entity_graph = entity_graph
    _event_bus = event_bus
    _context_memory = context_memory
    _action_engine = action_engine
    if _INTELLIGENCE_AVAILABLE:
        logger.info(
            "intelligence_hooks_initialized",
            entity_graph=bool(_entity_graph),
            event_bus=bool(_event_bus),
            context_memory=bool(_context_memory),
            action_engine=bool(_action_engine),
        )
    _register_event_subscribers()


def _register_event_subscribers() -> None:
    """Subscribe intelligence-aware alert handlers to the event bus."""
    if not _INTELLIGENCE_AVAILABLE or _event_bus is None:
        return
    try:
        _event_bus.subscribe("competitor.updated", _on_competitor_updated)
        _event_bus.subscribe("topic.anomaly_detected", _on_topic_anomaly)
        _event_bus.subscribe("search.potential_competitor_detected", _on_potential_competitor)
        _event_bus.subscribe("search.competitor_mentioned", _on_competitor_mentioned)
        logger.info("intelligence_event_subscribers_registered")
    except Exception as exc:
        logger.warning("intelligence_subscriber_registration_failed", error=str(exc))


def _safe_publish(event_type: str, source: str, payload: dict, priority: str = "normal") -> None:
    """Publish an event if the event bus is available."""
    if _event_bus is None:
        return
    try:
        _event_bus.publish(event_type, source, payload, priority=priority)
    except Exception as exc:
        logger.warning("intelligence_hook_publish_failed", error=str(exc))


def _safe_add_entity(entity_type: str, entity_id: str, name: str, data: dict) -> None:
    """Add an entity if the entity graph is available."""
    if _entity_graph is None:
        return
    try:
        _entity_graph.add_entity(entity_type, entity_id, name, data)
    except Exception as exc:
        logger.warning("intelligence_hook_entity_add_failed", error=str(exc))


def _safe_update_entity(entity_type: str, entity_id: str, data: dict) -> None:
    """Update an entity if the entity graph is available."""
    if _entity_graph is None:
        return
    try:
        _entity_graph.update_entity_data(entity_type, entity_id, data)
    except Exception as exc:
        logger.warning("intelligence_hook_entity_update_failed", error=str(exc))


def _safe_generate_actions(event: dict) -> list[dict]:
    """Generate actions if the action engine is available."""
    if _action_engine is None:
        return []
    try:
        return _action_engine.generate_actions(event)
    except Exception as exc:
        logger.warning("intelligence_hook_action_generation_failed", error=str(exc))
        return []


# ---------------------------------------------------------------------------
# Competitor hooks
# ---------------------------------------------------------------------------


def on_competitor_created(competitor: Any) -> None:
    """Hook called after a competitor is created."""
    if not _INTELLIGENCE_AVAILABLE:
        return
    try:
        competitor_id = str(competitor.id)
        name = competitor.name or competitor_id
        data = {
            "domain": getattr(competitor, "website_url", None),
            "industry": getattr(competitor, "industry", None),
            "status": "active",
        }
        _safe_add_entity("competitor", competitor_id, name, data)

        payload = {
            "competitor_id": competitor_id,
            "name": name,
            "domain": data["domain"],
            "industry": data["industry"],
        }
        _safe_publish("competitor.added", "competitor", payload)
        _safe_generate_actions({"type": "competitor.added", "payload": payload})
    except Exception as exc:
        logger.warning("intelligence_hook_competitor_created_failed", error=str(exc))


def on_competitor_updated(competitor: Any, old_data: dict | None = None) -> None:
    """Hook called after a competitor is updated."""
    if not _INTELLIGENCE_AVAILABLE:
        return
    try:
        competitor_id = str(competitor.id)
        name = competitor.name or competitor_id
        new_data = {
            "domain": getattr(competitor, "website_url", None),
            "industry": getattr(competitor, "industry", None),
            "status": getattr(competitor, "is_active", True) and "active" or "inactive",
        }
        _safe_update_entity("competitor", competitor_id, new_data)

        diff = {}
        if old_data:
            for key, value in new_data.items():
                if old_data.get(key) != value:
                    diff[key] = {"old": old_data.get(key), "new": value}

        significant = bool(diff)
        payload = {
            "competitor_id": competitor_id,
            "competitor_name": name,
            "changes": diff,
            "significant": significant,
        }
        _safe_publish(
            "competitor.updated",
            "competitor",
            payload,
            priority="high" if significant else "normal",
        )
        if significant:
            _safe_generate_actions({"type": "competitor.updated", "payload": payload})
    except Exception as exc:
        logger.warning("intelligence_hook_competitor_updated_failed", error=str(exc))


def on_competitor_deleted(competitor_id: Any) -> None:
    """Hook called after a competitor is deleted."""
    if not _INTELLIGENCE_AVAILABLE:
        return
    try:
        _safe_publish("competitor.removed", "competitor", {"competitor_id": str(competitor_id)})
    except Exception as exc:
        logger.warning("intelligence_hook_competitor_deleted_failed", error=str(exc))


# ---------------------------------------------------------------------------
# Search hooks
# ---------------------------------------------------------------------------


def _extract_entities_from_results(results: list[Any]) -> list[dict]:
    """Heuristic extraction of company/topic candidates from search results."""
    entities: list[dict] = []
    seen: set[str] = set()

    for result in results:
        title = getattr(result, "title", "") or ""
        snippet = getattr(result, "snippet", "") or ""
        text = f"{title} {snippet}"

        # Simple domain -> company heuristic.
        url = getattr(result, "url", "") or ""
        if url and "." in url:
            from urllib.parse import urlparse

            domain = urlparse(url).netloc.replace("www.", "").split(":")[0]
            if domain and domain not in seen:
                seen.add(domain)
                entities.append(
                    {
                        "type": "company",
                        "id": domain.replace(".", "_"),
                        "name": domain,
                        "data": {"domain": domain, "source_url": url},
                        "context": snippet[:200],
                    }
                )

        # Keyword/phrase candidates for topics.
        words = [w.lower() for w in title.split() if len(w) > 4]
        for word in words[:3]:
            key = f"topic:{word}"
            if key not in seen:
                seen.add(key)
                entities.append(
                    {
                        "type": "topic",
                        "id": word,
                        "name": word,
                        "data": {"term": word, "context": snippet[:200]},
                    }
                )

    return entities


def _count_mentions(name: str, results: list[Any]) -> int:
    """Count how many search results mention ``name``."""
    count = 0
    target = name.lower()
    for result in results:
        text = f"{getattr(result, 'title', '')} {getattr(result, 'snippet', '')}".lower()
        if target in text:
            count += 1
    return count


def _extract_trending_terms(results: list[Any]) -> dict[str, int]:
    """Return a simple frequency map of prominent terms in result titles."""
    frequencies: dict[str, int] = {}
    for result in results:
        title = getattr(result, "title", "") or ""
        for word in title.split():
            clean = "".join(c for c in word if c.isalnum()).lower()
            if len(clean) > 5:
                frequencies[clean] = frequencies.get(clean, 0) + 1
    return frequencies


def on_search_executed(query: str, results: list[Any], organization_id: int | None = None) -> None:
    """Hook called after a search is executed."""
    if not _INTELLIGENCE_AVAILABLE:
        return
    try:
        entities_found = _extract_entities_from_results(results)
        search_id = f"search_{hash(query + str(organization_id)) & 0xFFFFFFFF:08x}"

        _safe_publish(
            "search.executed",
            "search",
            {
                "query": query,
                "results_count": len(results),
                "top_entities": [
                    {"type": e["type"], "id": e["id"], "name": e["name"]} for e in entities_found[:10]
                ],
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            },
        )

        _safe_add_entity(
            "search",
            search_id,
            query,
            {"results_count": len(results), "organization_id": organization_id},
        )

        for entity in entities_found:
            entity_type = entity.get("type")
            entity_id = entity.get("id")
            if not entity_type or not entity_id:
                continue

            if entity_type == "company":
                existing = _entity_graph.find_by_keyword(entity["name"]) if _entity_graph else []
                competitor_matches = [e for e in existing if e.get("type") == "competitor"]
                if competitor_matches:
                    _safe_publish(
                        "search.competitor_mentioned",
                        "search",
                        {
                            "competitor_id": competitor_matches[0]["id"],
                            "competitor_name": entity["name"],
                            "query": query,
                            "context": entity.get("context", ""),
                        },
                    )
                else:
                    mention_count = _count_mentions(entity["name"], results)
                    if mention_count >= 2:
                        _safe_publish(
                            "search.potential_competitor_detected",
                            "search",
                            {
                                "company_name": entity["name"],
                                "mention_count": mention_count,
                                "query": query,
                                "sample_contexts": [entity.get("context", "")],
                            },
                        )

            if entity_type == "topic":
                _safe_link_entities("search", search_id, entity_type, entity_id, "found_in")

        trending_terms = _extract_trending_terms(results)
        for term, frequency in trending_terms.items():
            if _entity_graph:
                existing = _entity_graph.find_by_keyword(term)
                topic_matches = [e for e in existing if e.get("type") == "topic"]
                if topic_matches:
                    _safe_publish(
                        "search.topic_trending",
                        "search",
                        {"topic_id": topic_matches[0]["id"], "term": term, "query": query},
                    )
                else:
                    _safe_publish(
                        "search.new_topic_candidate",
                        "search",
                        {"term": term, "query": query, "frequency": frequency},
                    )
    except Exception as exc:
        logger.warning("intelligence_hook_search_executed_failed", error=str(exc))


def _safe_link_entities(
    from_type: str, from_id: str, to_type: str, to_id: str, relationship: str
) -> None:
    """Link two entities if the entity graph is available."""
    if _entity_graph is None:
        return
    try:
        _entity_graph.link_entities(from_type, from_id, to_type, to_id, relationship)
    except Exception as exc:
        logger.warning("intelligence_hook_link_failed", error=str(exc))


# ---------------------------------------------------------------------------
# Topic hooks
# ---------------------------------------------------------------------------


def on_topic_created(topic: Any) -> None:
    """Hook called after a topic workspace is created."""
    if not _INTELLIGENCE_AVAILABLE:
        return
    try:
        topic_id = str(topic.id)
        name = topic.name or topic_id
        data = {
            "status": getattr(topic, "status", "active"),
            "keywords": getattr(topic, "keywords", None),
            "organization_id": getattr(topic, "organization_id", None),
        }
        _safe_add_entity("topic", topic_id, name, data)
        _safe_publish(
            "topic.created",
            "topics",
            {
                "topic_id": topic_id,
                "name": name,
                "volume": 0,
                "sentiment": "neutral",
            },
        )
    except Exception as exc:
        logger.warning("intelligence_hook_topic_created_failed", error=str(exc))


def on_topic_updated(topic: Any, old_data: dict | None = None) -> None:
    """Hook called after a topic workspace is updated."""
    if not _INTELLIGENCE_AVAILABLE:
        return
    try:
        topic_id = str(topic.id)
        name = topic.name or topic_id
        new_data = {
            "status": getattr(topic, "status", "active"),
            "keywords": getattr(topic, "keywords", None),
            "organization_id": getattr(topic, "organization_id", None),
        }
        _safe_update_entity("topic", topic_id, new_data)

        old_volume = (old_data or {}).get("volume", 0)
        new_volume = new_data.get("volume", 0) or old_volume
        change_pct = ((new_volume - old_volume) / old_volume * 100) if old_volume else 0

        _safe_publish(
            "topic.updated",
            "topics",
            {
                "topic_id": topic_id,
                "old_volume": old_volume,
                "new_volume": new_volume,
                "change_pct": change_pct,
                "sentiment": "neutral",
            },
        )

        if abs(change_pct) > 20:
            direction = "up" if change_pct > 0 else "down"
            anomaly_event = {
                "type": "topic.anomaly_detected",
                "payload": {
                    "topic_id": topic_id,
                    "topic_name": name,
                    "direction": direction,
                    "change_pct": abs(change_pct),
                    "previous_volume": old_volume,
                    "current_volume": new_volume,
                },
            }
            _safe_publish(
                "topic.anomaly_detected",
                "topics",
                anomaly_event["payload"],
                priority="high" if abs(change_pct) > 50 else "normal",
            )
            _safe_generate_actions(anomaly_event)
    except Exception as exc:
        logger.warning("intelligence_hook_topic_updated_failed", error=str(exc))


def on_topic_deleted(topic_id: str) -> None:
    """Hook called after a topic workspace is deleted."""
    if not _INTELLIGENCE_AVAILABLE:
        return
    try:
        _safe_publish("topic.removed", "topics", {"topic_id": topic_id})
    except Exception as exc:
        logger.warning("intelligence_hook_topic_deleted_failed", error=str(exc))


def on_topic_analyzed(topic: Any, run: Any) -> None:
    """Hook called after an analysis run completes for a topic."""
    if not _INTELLIGENCE_AVAILABLE:
        return
    try:
        topic_id = str(topic.id)
        volume = 0
        sentiment = "neutral"
        if run and getattr(run, "results", None):
            for result in run.results:
                if getattr(result, "result_type", None) == "trends":
                    details = getattr(result, "details", {}) or {}
                    volume = details.get("volume", volume)
                if getattr(result, "result_type", None) == "sentiment":
                    score = getattr(result, "score", None)
                    if score is not None:
                        sentiment = "positive" if score > 0.2 else "negative" if score < -0.2 else "neutral"

        data = {
            "last_analysis_status": getattr(run, "status", "completed"),
            "volume": volume,
            "sentiment": sentiment,
        }
        _safe_update_entity("topic", topic_id, data)
        _safe_publish(
            "topic.updated",
            "topics",
            {
                "topic_id": topic_id,
                "name": topic.name,
                "volume": volume,
                "sentiment": sentiment,
            },
        )
    except Exception as exc:
        logger.warning("intelligence_hook_topic_analyzed_failed", error=str(exc))


# ---------------------------------------------------------------------------
# Alert hooks
# ---------------------------------------------------------------------------


def on_alert_created(alert: Any) -> None:
    """Hook called after an alert is created."""
    if not _INTELLIGENCE_AVAILABLE:
        return
    try:
        alert_id = str(alert.id)
        title = alert.title or f"Alert {alert_id}"
        _safe_add_entity(
            "alert",
            alert_id,
            title,
            {
                "priority": getattr(alert, "severity", "normal"),
                "source": "alert_service",
                "status": getattr(alert, "status", "open"),
            },
        )
        payload = {
            "alert_id": alert_id,
            "title": title,
            "description": getattr(alert, "message", ""),
            "urgency": 7 if getattr(alert, "severity", "") == "critical" else 5,
        }
        _safe_publish("alert.created", "alerts", payload, priority=payload["urgency"] >= 7 and "high" or "normal")
        _safe_generate_actions({"type": "alert.created", "payload": payload})
    except Exception as exc:
        logger.warning("intelligence_hook_alert_created_failed", error=str(exc))


# ---------------------------------------------------------------------------
# Report hooks
# ---------------------------------------------------------------------------


def on_report_created(report: Any) -> None:
    """Hook called after a report is generated."""
    if not _INTELLIGENCE_AVAILABLE:
        return
    try:
        report_id = str(report.id)
        title = report.title or f"Report {report_id}"
        _safe_add_entity(
            "report",
            report_id,
            title,
            {
                "format": getattr(report, "format", "markdown"),
                "status": getattr(report, "status", "completed"),
                "topic_id": getattr(report, "topic_id", None),
            },
        )
        _safe_publish(
            "report.created",
            "reports",
            {
                "report_id": report_id,
                "title": title,
                "status": getattr(report, "status", "completed"),
            },
        )
    except Exception as exc:
        logger.warning("intelligence_hook_report_created_failed", error=str(exc))


# ---------------------------------------------------------------------------
# Provider / AI hooks
# ---------------------------------------------------------------------------


def enrich_provider_prompt(session_id: str | None, prompt: str) -> str:
    """Enrich a provider prompt with session context and entity awareness."""
    if not _INTELLIGENCE_AVAILABLE or not session_id or _context_memory is None:
        return prompt
    try:
        enriched = _context_memory.build_prompt_context(session_id, prompt)

        entity_mention = _detect_entity_in_prompt(prompt)
        if entity_mention and _entity_graph is not None:
            entity_context = _context_memory.get_entity_aware_context(
                session_id,
                entity_mention["type"],
                entity_mention["id"],
                _entity_graph,
            )
            enriched = f"{enriched}\n\n[ENTITY CONTEXT]\n{entity_context}"

        return enriched
    except Exception as exc:
        logger.warning("intelligence_hook_prompt_enrichment_failed", error=str(exc))
        return prompt


def store_provider_context(session_id: str | None, prompt: str, response: Any) -> None:
    """Store a provider interaction in session context memory."""
    if not _INTELLIGENCE_AVAILABLE or not session_id or _context_memory is None:
        return
    try:
        summary = response[:200] if isinstance(response, str) else str(response)[:200]
        _context_memory.store_context(
            session_id,
            "ai_provider",
            {
                "query": prompt,
                "response_summary": summary,
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            },
        )
    except Exception as exc:
        logger.warning("intelligence_hook_context_storage_failed", error=str(exc))


def _detect_entity_in_prompt(prompt: str) -> dict | None:
    """Naive entity detection for competitor/topic mentions in prompts."""
    if _entity_graph is None:
        return None
    try:
        for keyword in prompt.split():
            clean = "".join(c for c in keyword if c.isalnum()).lower()
            if len(clean) < 4:
                continue
            matches = _entity_graph.find_by_keyword(clean)
            for match in matches:
                if match.get("type") in ("competitor", "topic", "company"):
                    return {"type": match["type"], "id": match["id"]}
    except Exception:
        pass
    return None


def generate_intelligence_brief(entity_type: str, entity_id: str) -> str:
    """Generate a plain-text intelligence brief for an entity if data exists."""
    if not _INTELLIGENCE_AVAILABLE or _entity_graph is None:
        return "Intelligence core not available."
    try:
        entity = _entity_graph.get_entity(entity_type, entity_id)
        if not entity:
            return f"No intelligence data found for {entity_type}:{entity_id}."
        related = _entity_graph.get_related(entity_type, entity_id)
        timeline = _entity_graph.get_entity_timeline(entity_type, entity_id, limit=10)
        lines = [
            f"Intelligence Brief: {entity.get('name', entity_id)} ({entity_type})",
            f"Data: {entity.get('data', {})}",
            f"Related entities: {len(related)}",
        ]
        for rel in related[:5]:
            lines.append(f"  - {rel.get('relationship')} {rel.get('type')}:{rel.get('id')}")
        if timeline:
            lines.append("Recent events:")
            for event in timeline[:5]:
                lines.append(f"  - {event.get('timestamp')} {event.get('type')}")
        return "\n".join(lines)
    except Exception as exc:
        logger.warning("intelligence_brief_failed", error=str(exc))
        return f"Could not generate brief: {exc}"

# ---------------------------------------------------------------------------
# Event-driven alert handlers
# ---------------------------------------------------------------------------


def _on_competitor_updated(event: dict) -> None:
    """React to competitor updates by creating graph alert entities and actions."""
    if not _INTELLIGENCE_AVAILABLE:
        return
    try:
        payload = event.get("payload", {})
        competitor_id = payload.get("competitor_id")
        competitor_name = payload.get("competitor_name", "Unknown")
        changes = payload.get("changes", {})
        significant = payload.get("significant", False)

        title = f"Competitor {competitor_name} updated"
        if "price" in changes:
            title = f"Price change detected: {competitor_name}"
        elif "product" in changes:
            title = f"New product from {competitor_name}"

        related = _entity_graph.get_related("competitor", competitor_id) if _entity_graph else []
        alert_id = f"alert_{__import__('uuid').uuid4().hex[:12]}"

        if _entity_graph:
            _entity_graph.add_entity(
                "alert",
                alert_id,
                title,
                {"priority": "high" if significant else "normal", "source": "competitor.updated"},
            )
            _entity_graph.link_entities("alert", alert_id, "competitor", competitor_id, "triggered_by")

        actions = _safe_generate_actions(event) if significant else []
        _safe_publish(
            "alert.created",
            "alerts",
            {
                "alert_id": alert_id,
                "title": title,
                "description": f"Changes: {changes}",
                "priority": "high" if significant else "normal",
                "source_modules": ["competitor"],
                "related_entities": related,
                "suggested_actions": actions,
                "urgency": 8 if significant else 5,
            },
            priority="high" if significant else "normal",
        )
    except Exception as exc:
        logger.warning("intelligence_on_competitor_updated_failed", error=str(exc))


def _on_topic_anomaly(event: dict) -> None:
    """React to topic anomalies and surface opportunity alerts."""
    if not _INTELLIGENCE_AVAILABLE:
        return
    try:
        payload = event.get("payload", {})
        topic_id = payload.get("topic_id", "")
        topic_name = payload.get("topic_name", "Unknown")
        direction = payload.get("direction", "up")
        change_pct = payload.get("change_pct", 0)

        title = f"Topic '{topic_name}' trending {direction} by {change_pct:.1f}%"
        related_competitors = _entity_graph.get_related("topic", topic_id) if _entity_graph else []
        competitor_count = len([r for r in related_competitors if r.get("type") == "competitor"])

        description = f"Topic volume changed from {payload.get('previous_volume', 0)} to {payload.get('current_volume', 0)}. "
        if competitor_count == 0:
            description += "No competitors active in this space. HIGH OPPORTUNITY."
        elif competitor_count < 3:
            description += f"Only {competitor_count} competitors active. Moderate opportunity."
        else:
            description += f"{competitor_count} competitors active. Competitive space."

        alert_id = f"alert_{__import__('uuid').uuid4().hex[:12]}"
        if _entity_graph:
            _entity_graph.add_entity(
                "alert",
                alert_id,
                title,
                {
                    "priority": "high" if change_pct > 50 else "normal",
                    "type": "opportunity" if competitor_count < 3 else "trend",
                },
            )
            _entity_graph.link_entities("alert", alert_id, "topic", topic_id, "triggered_by")

        actions = _safe_generate_actions(event)
        _safe_publish(
            "alert.created",
            "alerts",
            {
                "alert_id": alert_id,
                "title": title,
                "description": description,
                "priority": "high" if change_pct > 50 else "normal",
                "source_modules": ["topics"],
                "related_entities": related_competitors,
                "suggested_actions": actions,
                "opportunity_score": 10 - min(competitor_count, 10),
                "urgency": 8 if change_pct > 50 else 5,
            },
            priority="high" if change_pct > 50 else "normal",
        )
    except Exception as exc:
        logger.warning("intelligence_on_topic_anomaly_failed", error=str(exc))


def _on_potential_competitor(event: dict) -> None:
    """React to a newly detected potential competitor."""
    if not _INTELLIGENCE_AVAILABLE:
        return
    try:
        payload = event.get("payload", {})
        company_name = payload.get("company_name", "")
        mention_count = payload.get("mention_count", 0)
        query = payload.get("query", "")

        title = f"New competitor candidate: {company_name}"
        description = f"Detected {mention_count} mentions in search. Query: {query}"
        alert_id = f"alert_{__import__('uuid').uuid4().hex[:12]}"

        if _entity_graph:
            _entity_graph.add_entity("alert", alert_id, title, {"priority": "normal"})

        _safe_publish(
            "alert.created",
            "alerts",
            {
                "alert_id": alert_id,
                "title": title,
                "description": description,
                "priority": "normal",
                "source_modules": ["search"],
                "suggested_actions": [
                    {"type": "monitor_closely", "title": f"Monitor {company_name}"},
                    {"type": "generate_content_brief", "title": "Prepare competitive content"},
                ],
                "urgency": 4,
            },
        )
    except Exception as exc:
        logger.warning("intelligence_on_potential_competitor_failed", error=str(exc))


def _on_competitor_mentioned(event: dict) -> None:
    """React to competitor mentions in search results."""
    if not _INTELLIGENCE_AVAILABLE:
        return
    try:
        payload = event.get("payload", {})
        competitor_id = payload.get("competitor_id", "")
        competitor_name = payload.get("competitor_name", "")
        query = payload.get("query", "")
        context = payload.get("context", "")

        title = f"Competitor {competitor_name} mentioned in search"
        description = f"Query: {query}. Context: {context}"
        alert_id = f"alert_{__import__('uuid').uuid4().hex[:12]}"

        if _entity_graph:
            _entity_graph.add_entity("alert", alert_id, title, {"priority": "low"})
            _entity_graph.link_entities("alert", alert_id, "competitor", competitor_id, "triggered_by")

        _safe_publish(
            "alert.created",
            "alerts",
            {
                "alert_id": alert_id,
                "title": title,
                "description": description,
                "priority": "low",
                "source_modules": ["search", "competitor"],
                "urgency": 2,
            },
        )
    except Exception as exc:
        logger.warning("intelligence_on_competitor_mentioned_failed", error=str(exc))
