"""AI content generation service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.crud.provider import provider_repository
from app.models.user import User
from app.providers.registry import ProviderRegistry
from app.services.provider_service import provider_service

logger = get_logger(__name__)


class ContentService:
    """Service for generating marketing content with AI."""

    TEMPLATES: dict[str, str] = {
        "linkedin": "Write a professional LinkedIn post about: {topic}. Tone: {tone}. Length: ~150 words.",
        "x": "Write an engaging X/Twitter post about: {topic}. Tone: {tone}. Max 280 characters.",
        "instagram": "Write an Instagram caption about: {topic}. Tone: {tone}. Include relevant hashtags.",
        "blog": "Write a blog draft outline about: {topic}. Tone: {tone}. Include an introduction and 3-5 key sections.",
    }

    async def generate(
        self,
        db: AsyncSession,
        *,
        content_type: str,
        topic: str,
        tone: str,
        user: User,
        provider_id: int | None = None,
    ) -> dict[str, str]:
        """Generate content for a specific channel."""
        if content_type not in self.TEMPLATES:
            raise AppException(f"Unsupported content type: {content_type}")

        provider = await self._resolve_provider(db, user, provider_id)
        config = provider_service._build_runtime_config(provider)
        adapter = ProviderRegistry.create(provider.provider_type, config)
        model = provider.models[0].external_id if provider.models else ""
        if not model:
            raise AppException("No model available")

        prompt = self.TEMPLATES[content_type].format(topic=topic, tone=tone)
        response = await adapter.chat_completion(
            messages=[
                {"role": "system", "content": "You are a marketing copywriter."},
                {"role": "user", "content": prompt},
            ],
            model=model,
            temperature=0.8,
            max_tokens=1500,
        )
        await provider_service._record_cost(
            db,
            response.usage,
            organization_id=user.organization_id,
            user_id=user.id,
            provider_id=provider.id,
        )
        return {
            "content_type": content_type,
            "content": response.content,
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


content_service = ContentService()
