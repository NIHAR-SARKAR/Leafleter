"""Scheduled job handlers."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.job import Job
from app.models.organization import Organization
from app.services.analysis_service import analysis_service
from app.services.search_service import search_service

logger = get_logger(__name__)


async def re_analysis_job(
    db: AsyncSession,
    *,
    organization_id: int,
    topic_id: int,
    config: dict[str, Any],
) -> None:
    """Re-run analysis on a topic."""
    from app.crud.topic import topic_repository

    topic = await topic_repository.get_or_404_for_organization(
        db, topic_id, organization_id
    )
    from app.models.user import User
    from app.schemas.topic import TopicAnalyzeRequest

    user = await db.get(User, config.get("user_id"))
    if user is None:
        raise ValueError("User not found for scheduled analysis")
    await analysis_service.run_analysis(
        db,
        topic=topic,
        obj_in=TopicAnalyzeRequest(
            analysis_types=config.get("analysis_types", ["sentiment"]),
            provider_id=config.get("provider_id"),
            model=config.get("model"),
        ),
        user=user,
    )


async def report_generation_job(
    db: AsyncSession,
    *,
    organization_id: int,
    topic_id: int,
    config: dict[str, Any],
) -> None:
    """Generate a scheduled report."""
    from app.crud.topic import topic_repository
    from app.schemas.report import ReportCreate
    from app.services.report_service import report_service

    topic = await topic_repository.get_or_404_for_organization(
        db, topic_id, organization_id
    )
    from app.models.user import User

    user = await db.get(User, config.get("user_id"))
    if user is None:
        raise ValueError("User not found for scheduled report")
    await report_service.create_report(
        db,
        obj_in=ReportCreate(
            title=config.get("title", f"Scheduled Report - {topic.name}"),
            report_type="scheduled",
            format=config.get("format", "markdown"),
            topic_id=topic.id,
        ),
        user=user,
    )


async def competitor_snapshot_job(
    db: AsyncSession,
    *,
    organization_id: int,
    competitor_id: int,
    config: dict[str, Any],
) -> None:
    """Take a competitor snapshot."""
    from app.crud.base import BaseRepository
    from app.models.competitor import Competitor, CompetitorSnapshot

    competitor_repo = BaseRepository(Competitor)
    competitor = await competitor_repo.get_or_404(db, competitor_id)
    if competitor.organization_id != organization_id:
        raise ValueError("Competitor not found")

    snapshot_type = config.get("snapshot_type", "website")
    content = ""
    if competitor.website_url and snapshot_type == "website":
        result = await search_service.crawl(competitor.website_url)
        content = result.text[:5000]

    snapshot_repo = BaseRepository(CompetitorSnapshot)
    await snapshot_repo.create(
        db,
        obj_in={
            "competitor_id": competitor.id,
            "snapshot_type": snapshot_type,
            "source_url": competitor.website_url,
            "content": content,
            "metrics": {},
        },
    )
    await db.commit()


async def competitor_feature_monitor_job(
    db: AsyncSession,
    *,
    organization_id: int,
    competitor_id: int,
    config: dict[str, Any],
) -> None:
    """Monitor competitor features and generate a comparison report."""
    from app.crud.competitor import competitor_repository
    from app.models.organization import Organization
    from app.schemas.competitor import CompetitorFeatureComparisonCreate
    from app.services.competitor_feature_service import competitor_feature_service

    competitor = await competitor_repository.get_or_404(db, competitor_id)
    if competitor.organization_id != organization_id:
        raise ValueError("Competitor not found")

    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise ValueError("Organization not found")

    title = config.get("title") or f"Scheduled Feature Comparison: {competitor.name}"
    await competitor_feature_service.run_comparison(
        db,
        competitor=competitor,
        organization=organization,
        obj_in=CompetitorFeatureComparisonCreate(
            title=title,
            report_format=config.get("report_format", "docx"),
        ),
    )


async def brand_monitor_job(
    db: AsyncSession,
    *,
    organization_id: int,
    topic_id: int,
    config: dict[str, Any],
) -> None:
    """Monitor brand mentions for a topic."""
    from app.crud.topic import topic_repository

    topic = await topic_repository.get_or_404_for_organization(
        db, topic_id, organization_id
    )
    query = config.get("query") or topic.name
    engine_type = config.get("engine_type", "serpapi")
    await search_service.add_search_source(
        db,
        topic_id=topic.id,
        query=query,
        engine_type=engine_type,
        organization_id=organization_id,
    )


async def newsletter_job(
    db: AsyncSession,
    *,
    organization_id: int,
    config: dict[str, Any],
) -> None:
    """Build and send a scheduled newsletter digest."""
    from app.services.newsletter_service import newsletter_service

    await newsletter_service.run_scheduled_newsletter(
        db, organization_id=organization_id, config=config
    )


async def intelligence_ingestion_job(
    db: AsyncSession,
    *,
    organization_id: int,
    config: dict[str, Any],
) -> None:
    """Run intelligence ingestion for all active sources in an organization."""
    from app.services.intelligence_ingestion_service import (
        intelligence_ingestion_service,
    )

    source_id = config.get("source_id")
    if source_id:
        from app.crud.intelligence import intelligence_source_repository

        source = await intelligence_source_repository.get_or_404(db, source_id)
        if source.organization_id != organization_id:
            raise ValueError("Source not found")
        organization = await db.get(Organization, organization_id)
        if organization is None:
            raise ValueError("Organization not found")
        await intelligence_ingestion_service.ingest_source(
            db, source=source, organization=organization
        )
    else:
        await intelligence_ingestion_service.ingest_all_active_sources(
            db, organization_id=organization_id
        )


async def execute_job(
    db: AsyncSession,
    *,
    job_id: int,
    job_type: str,
    organization_id: int,
    config: dict[str, Any],
) -> None:
    """Execute a job and update its status."""
    repo = BaseRepository(Job)
    job = await repo.get_or_404(db, job_id)
    job.status = "running"
    job.started_at = datetime.now(UTC)
    await db.commit()

    try:
        if job_type == "re_analysis":
            await re_analysis_job(db, organization_id=organization_id, topic_id=config["topic_id"], config=config)
        elif job_type == "report_generation":
            await report_generation_job(db, organization_id=organization_id, topic_id=config["topic_id"], config=config)
        elif job_type == "competitor_snapshot":
            await competitor_snapshot_job(db, organization_id=organization_id, competitor_id=config["competitor_id"], config=config)
        elif job_type == "competitor_feature_monitor":
            await competitor_feature_monitor_job(db, organization_id=organization_id, competitor_id=config["competitor_id"], config=config)
        elif job_type == "brand_monitor":
            await brand_monitor_job(db, organization_id=organization_id, topic_id=config["topic_id"], config=config)
        elif job_type == "intelligence_ingestion":
            await intelligence_ingestion_job(db, organization_id=organization_id, config=config)
        elif job_type == "newsletter":
            await newsletter_job(db, organization_id=organization_id, config=config)
        else:
            raise ValueError(f"Unknown job type: {job_type}")

        job.status = "completed"
        job.result_summary = "Job completed successfully"
    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        logger.exception("job_execution_failed", job_id=job_id, error=str(exc))
    finally:
        job.completed_at = datetime.now(UTC)
        await db.commit()
