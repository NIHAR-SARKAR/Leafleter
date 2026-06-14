"""AI debate engine service."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.crud.provider import provider_repository
from app.models.topic import Topic
from app.models.user import User
from app.providers.base import ProviderResponse
from app.providers.registry import ProviderRegistry
from app.services.provider_service import provider_service

logger = get_logger(__name__)


class DebateService:
    """Service for running multi-provider AI debates."""

    async def debate(
        self,
        db: AsyncSession,
        *,
        topic: Topic,
        question: str,
        provider_ids: list[int],
        user: User,
    ) -> dict[str, Any]:
        """Run multiple AI models on the same question and synthesize consensus."""
        if len(provider_ids) < 2:
            raise AppException("At least two providers are required for a debate")

        providers = []
        for pid in provider_ids:
            provider = await provider_repository.get(db, pid)
            if provider and provider.organization_id == user.organization_id:
                providers.append(provider)

        if len(providers) < 2:
            raise AppException("At least two valid providers required", status_code=400)

        responses: list[dict[str, Any]] = []
        total_cost = 0.0

        for provider in providers:
            config = provider_service._build_runtime_config(provider)
            adapter = ProviderRegistry.create(provider.provider_type, config)
            model = provider.models[0].external_id if provider.models else ""
            if not model:
                continue
            messages = [
                {
                    "role": "system",
                    "content": "You are participating in a multi-model debate. Provide a concise analysis.",
                },
                {
                    "role": "user",
                    "content": f"Topic: {topic.name}\nQuestion: {question}",
                },
            ]
            try:
                response = await adapter.chat_completion(
                    messages=messages,
                    model=model,
                    temperature=0.5,
                    max_tokens=1500,
                )
                responses.append(
                    {
                        "provider": provider.name,
                        "provider_type": provider.provider_type,
                        "model": model,
                        "content": response.content,
                    }
                )
                total_cost += response.usage.cost
                await provider_service._record_cost(
                    db,
                    response.usage,
                    organization_id=user.organization_id,
                    user_id=user.id,
                    provider_id=provider.id,
                )
            except Exception as exc:
                logger.warning("debate_provider_failed", provider_id=provider.id, error=str(exc))
                responses.append(
                    {
                        "provider": provider.name,
                        "provider_type": provider.provider_type,
                        "model": model,
                        "error": str(exc),
                    }
                )

        consensus = await self._synthesize_consensus(db, topic, question, responses, user)
        return {
            "topic_id": topic.id,
            "question": question,
            "responses": responses,
            "consensus": consensus,
            "total_cost": total_cost,
        }

    async def _synthesize_consensus(
        self,
        db: AsyncSession,
        topic: Topic,
        question: str,
        responses: list[dict[str, Any]],
        user: User,
    ) -> str:
        """Use the default provider to synthesize a consensus report."""
        provider = await provider_repository.get_default_for_organization(
            db, user.organization_id
        )
        if provider is None:
            return "Consensus synthesis requires a default provider."

        config = provider_service._build_runtime_config(provider)
        adapter = ProviderRegistry.create(provider.provider_type, config)
        model = provider.models[0].external_id if provider.models else ""
        if not model:
            return "No model available for consensus synthesis."

        combined = "\n\n".join(
            f"Provider {r['provider']}:\n{r.get('content', '')}"
            for r in responses
            if "content" in r
        )
        messages = [
            {
                "role": "system",
                "content": "Synthesize the following expert analyses into a concise consensus report.",
            },
            {
                "role": "user",
                "content": f"Topic: {topic.name}\nQuestion: {question}\n\n{combined}",
            },
        ]
        response = await adapter.chat_completion(
            messages=messages,
            model=model,
            temperature=0.3,
            max_tokens=2000,
        )
        await provider_service._record_cost(
            db,
            response.usage,
            organization_id=user.organization_id,
            user_id=user.id,
            provider_id=provider.id,
        )
        return response.content


debate_service = DebateService()
