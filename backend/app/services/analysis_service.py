"""Topic analysis service."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.audience import AudienceAnalysisEngine
from app.analysis.base import AnalysisContext
from app.analysis.reputation import ReputationAnalysisEngine
from app.analysis.sentiment import SentimentAnalysisEngine
from app.analysis.swot import SWOTAnalysisEngine
from app.analysis.trends import TrendAnalysisEngine
from app.core.exceptions import AppException, NotFoundException
from app.core.logging import get_logger
from app.crud.provider import provider_repository
from app.crud.topic import (
    analysis_result_repository,
    analysis_run_repository,
    topic_source_repository,
)
from app.models.topic import AnalysisRun, Topic
from app.models.user import User
from app.providers.base import ProviderUsage
from app.providers.registry import ProviderRegistry
from app.schemas.topic import TopicAnalyzeRequest
from app.services.provider_service import provider_service

logger = get_logger(__name__)

ANALYSIS_ENGINES: dict[str, type] = {
    "sentiment": SentimentAnalysisEngine,
    "trends": TrendAnalysisEngine,
    "swot": SWOTAnalysisEngine,
    "audience": AudienceAnalysisEngine,
    "reputation": ReputationAnalysisEngine,
    "pain_points": AudienceAnalysisEngine,
    "opportunities": SWOTAnalysisEngine,
}


class AnalysisService:
    """Service for running AI analyses on topic workspaces."""

    async def run_analysis(
        self,
        db: AsyncSession,
        *,
        topic: Topic,
        obj_in: TopicAnalyzeRequest,
        user: User,
    ) -> AnalysisRun:
        """Run one or more analyses for a topic."""
        provider = await self._resolve_provider(db, user, obj_in.provider_id)
        config = provider_service._build_runtime_config(provider)
        adapter = ProviderRegistry.create(provider.provider_type, config)
        model = obj_in.model or (
            provider.models[0].external_id if provider.models else ""
        )
        if not model:
            raise AppException("No model available for provider", status_code=400)

        sources_text = await self._build_sources_text(db, topic)

        run = await analysis_run_repository.create(
            db,
            obj_in={
                "analysis_type": ",".join(obj_in.analysis_types),
                "status": "running",
                "topic_id": topic.id,
                "provider_id": provider.id,
                "configuration": obj_in.model_dump(),
            },
        )
        await db.commit()

        context = AnalysisContext(
            topic=topic,
            provider=adapter,
            model=model,
            sources_text=sources_text,
        )

        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0

        try:
            for analysis_type in obj_in.analysis_types:
                engine_class = ANALYSIS_ENGINES.get(analysis_type)
                if engine_class is None:
                    logger.warning("unknown_analysis_type", analysis_type=analysis_type)
                    continue
                engine = engine_class()
                result_data = await engine.analyze(context)

                usage = result_data.get("usage")
                if usage:
                    total_input_tokens += usage.input_tokens
                    total_output_tokens += usage.output_tokens
                    total_cost += usage.cost

                await analysis_result_repository.create(
                    db,
                    obj_in={
                        "result_type": result_data["result_type"],
                        "score": result_data.get("score"),
                        "summary": result_data.get("summary"),
                        "details": result_data.get("details"),
                        "raw_output": result_data.get("raw_output"),
                        "run_id": run.id,
                    },
                )

            run.status = "completed"
            run.input_tokens = total_input_tokens
            run.output_tokens = total_output_tokens
            run.cost = total_cost
            run.completed_at = datetime.now(timezone.utc)
            db.add(run)
            await db.commit()
            await db.refresh(run)

            usage = ProviderUsage(
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                total_tokens=total_input_tokens + total_output_tokens,
                cost=total_cost,
                model=model,
                provider_type=provider.provider_type,
            )
            await provider_service._record_cost(
                db,
                usage,
                organization_id=user.organization_id,
                user_id=user.id,
                provider_id=provider.id,
            )
        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            db.add(run)
            await db.commit()
            await db.refresh(run)
            raise

        return run

    async def _resolve_provider(
        self,
        db: AsyncSession,
        user: User,
        provider_id: int | None,
    ) -> Any:
        """Resolve the provider to use for analysis."""
        if provider_id:
            provider = await provider_repository.get(db, provider_id)
            if provider is None or provider.organization_id != user.organization_id:
                raise NotFoundException("Provider not found")
            return provider

        provider = await provider_repository.get_default_for_organization(
            db, user.organization_id
        )
        if provider is None:
            raise AppException("No active AI provider configured", status_code=400)
        return provider

    async def _build_sources_text(self, db: AsyncSession, topic: Topic) -> str:
        """Build a text blob from topic sources for analysis prompts."""
        sources = await topic_source_repository.get_by_topic(db, topic.id)
        sources_text_parts: list[str] = []
        for source in sources:
            text = source.raw_data or source.query or source.url or ""
            sources_text_parts.append(f"Source: {source.name}\n{text[:2000]}")
        return "\n\n".join(sources_text_parts) or "No sources collected yet."


analysis_service = AnalysisService()
