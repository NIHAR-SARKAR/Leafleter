"""Campaign analyzer service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.crud.provider import provider_repository
from app.models.user import User
from app.providers.registry import ProviderRegistry
from app.services.provider_service import provider_service

logger = get_logger(__name__)


class CampaignService:
    """Service for analyzing campaign results with AI."""

    async def analyze(
        self,
        db: AsyncSession,
        *,
        campaign_name: str,
        description: str,
        metrics: str,
        user: User,
        provider_id: int | None = None,
    ) -> dict[str, str]:
        """Analyze campaign data and return AI feedback."""
        provider = await self._resolve_provider(db, user, provider_id)
        config = provider_service._build_runtime_config(provider)
        adapter = ProviderRegistry.create(provider.provider_type, config)
        model = provider.models[0].external_id if provider.models else ""
        if not model:
            raise AppException("No model available")

        prompt = f"""Analyze the following marketing campaign and provide actionable feedback.

Campaign: {campaign_name}
Description: {description}
Metrics/Results:
{metrics}

Provide:
1. Overall performance summary
2. Strengths
3. Weaknesses
4. Specific recommendations for improvement
"""
        response = await adapter.chat_completion(
            messages=[
                {"role": "system", "content": "You are a marketing analyst."},
                {"role": "user", "content": prompt},
            ],
            model=model,
            temperature=0.4,
            max_tokens=2000,
        )
        await provider_service._record_cost(
            db,
            response.usage,
            organization_id=user.organization_id,
            user_id=user.id,
            provider_id=provider.id,
        )
        return {
            "campaign_name": campaign_name,
            "analysis": response.content,
            "model": model,
            "cost": str(response.usage.cost),
        }

    async def _resolve_provider(
        self,
        db: AsyncSession,
        user: User,
        provider_id: int | None,
    ):
        if provider_id:
            provider = await provider_repository.get(db, provider_id)
            if provider is None or provider.organization_id != user.organization_id:
                raise AppException("Provider not found")
            return provider
        provider = await provider_repository.get_default_for_organization(
            db, user.organization_id
        )
        if provider is None:
            raise AppException("No active AI provider configured")
        return provider


campaign_service = CampaignService()
