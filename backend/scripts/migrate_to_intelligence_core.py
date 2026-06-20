#!/usr/bin/env python3
"""Migration script: seed the Intelligence Core graph from existing Leafleter data.

Run from the ``backend`` directory:

    python scripts/migrate_to_intelligence_core.py

This script reads competitors, topics, and alerts from the application database
and creates corresponding entities in the Intelligence Core graph.
"""

from __future__ import annotations

import asyncio
import os
import sys

# Allow running the script from the backend directory without installing the package.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.intelligence import init_intelligence_core
from app.db.session import AsyncSessionLocal
from app.crud.competitor import competitor_repository
from app.crud.topic import topic_repository
from app.crud.base import BaseRepository
from app.models.alert import Alert


async def migrate() -> None:
    """Migrate existing records into the Intelligence Core entity graph."""
    core = init_intelligence_core()
    if not core:
        print("Intelligence core could not be initialized.")
        return

    graph = core["entity_graph"]

    async with AsyncSessionLocal() as db:
        competitors = await competitor_repository.get_multi(db, limit=10000)
        for comp in competitors:
            graph.add_entity(
                "competitor",
                str(comp.id),
                comp.name or f"Competitor {comp.id}",
                {
                    "domain": comp.website_url,
                    "industry": getattr(comp, "industry", None),
                    "status": "active" if comp.is_active else "inactive",
                },
            )

        topics = await topic_repository.get_multi(db, limit=10000)
        for topic in topics:
            graph.add_entity(
                "topic",
                str(topic.id),
                topic.name or f"Topic {topic.id}",
                {
                    "status": topic.status,
                    "keywords": topic.keywords,
                    "organization_id": topic.organization_id,
                },
            )

        alert_repo = BaseRepository(Alert)
        alerts = await alert_repo.get_multi(db, limit=10000)
        for alert in alerts:
            graph.add_entity(
                "alert",
                str(alert.id),
                alert.title or f"Alert {alert.id}",
                {
                    "priority": alert.severity,
                    "status": alert.status,
                    "source": "alert_service",
                },
            )

    total = graph.count_entities()
    print(f"Migration complete. Entities: {total}")


if __name__ == "__main__":
    asyncio.run(migrate())
