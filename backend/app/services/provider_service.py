"""AI provider management service."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException, ConflictException, NotFoundException
from app.core.logging import get_logger
from app.crud.provider import provider_model_repository, provider_repository
from app.models.cost_ledger import CostLedger
from app.models.provider import Provider, ProviderModel
from app.models.user import User
from app.providers.base import ProviderResponse
from app.providers.registry import ProviderRegistry
from app.schemas.provider import ProviderChatRequest, ProviderCreate, ProviderUpdate
from app.services.intelligence_hooks import (
    enrich_provider_prompt,
    store_provider_context,
)
from app.utils.crypto import decrypt, encrypt

logger = get_logger(__name__)

PROVIDER_API_KEY_FIELDS: dict[str, str] = {
    "openai": "api_key",
    "anthropic": "api_key",
    "claude": "api_key",
    "gemini": "api_key",
    "openrouter": "api_key",
    "azure_openai": "api_key",
    "bedrock": "secret_key",
    "kimi": "api_key",
    "qwen": "api_key",
}


class ProviderService:
    """Service for managing AI providers and routing requests."""

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: ProviderCreate,
        organization_id: int,
        created_by: User,
    ) -> Provider:
        """Create a provider configuration for an organization."""
        data = obj_in.model_dump(exclude={"api_key", "models"})
        data["organization_id"] = organization_id
        data["created_by_id"] = created_by.id

        config = data.get("config") or {}
        api_key = obj_in.api_key
        if api_key:
            data["api_key_encrypted"] = encrypt(api_key)
            config[PROVIDER_API_KEY_FIELDS.get(obj_in.provider_type, "api_key")] = api_key
        data["config"] = config

        provider = await provider_repository.create(db, obj_in=data)

        for model_in in obj_in.models:
            await provider_model_repository.create(
                db,
                obj_in={
                    **model_in.model_dump(),
                    "provider_id": provider.id,
                },
            )

        await db.commit()
        await db.refresh(provider)
        logger.info(
            "provider_created",
            provider_id=provider.id,
            organization_id=organization_id,
        )
        return provider

    async def update(
        self,
        db: AsyncSession,
        *,
        provider: Provider,
        obj_in: ProviderUpdate,
    ) -> Provider:
        """Update a provider configuration."""
        update_data = obj_in.model_dump(exclude_unset=True, exclude={"api_key"})
        api_key = obj_in.api_key if obj_in.api_key is not None else None

        if api_key:
            update_data["api_key_encrypted"] = encrypt(api_key)
            config = update_data.get("config") or provider.config or {}
            config[PROVIDER_API_KEY_FIELDS.get(provider.provider_type, "api_key")] = api_key
            update_data["config"] = config

        provider = await provider_repository.update(db, db_obj=provider, obj_in=update_data)
        await db.commit()
        await db.refresh(provider)
        logger.info("provider_updated", provider_id=provider.id)
        return provider

    async def delete(self, db: AsyncSession, *, provider: Provider) -> None:
        """Soft delete a provider."""
        await provider_repository.delete(db, db_obj=provider)
        await db.commit()
        logger.info("provider_deleted", provider_id=provider.id)

    async def test_connection(
        self,
        db: AsyncSession,
        *,
        provider: Provider,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """Test provider credentials and return available models."""
        config = self._build_runtime_config(provider, override_key=api_key)
        try:
            adapter = ProviderRegistry.create(provider.provider_type, config)
            valid = await adapter.validate_credentials()
            models = await adapter.list_models() if valid else []
            return {
                "success": valid,
                "message": "Connection successful" if valid else "Connection failed",
                "models": models,
            }
        except Exception as exc:
            logger.warning(
                "provider_test_failed",
                provider_id=provider.id,
                error=str(exc),
            )
            return {
                "success": False,
                "message": f"Connection failed: {exc}",
                "models": [],
            }

    async def chat(
        self,
        db: AsyncSession,
        *,
        provider: Provider,
        obj_in: ProviderChatRequest,
        user: User,
    ) -> ProviderResponse:
        """Execute a direct chat request through a provider."""
        config = self._build_runtime_config(provider)
        adapter = ProviderRegistry.create(provider.provider_type, config)

        messages = obj_in.messages
        session_id = obj_in.session_id
        if session_id and messages:
            try:
                last_user_message = messages[-1].get("content", "")
                enriched = enrich_provider_prompt(session_id, last_user_message)
                messages = messages[:-1] + [{**messages[-1], "content": enriched}]
            except Exception as exc:
                logger.warning("provider_context_enrichment_failed", error=str(exc))

        response = await adapter.chat_completion(
            messages=messages,
            model=obj_in.model,
            temperature=obj_in.temperature,
            max_tokens=obj_in.max_tokens,
        )

        if session_id and messages:
            try:
                last_user_message = messages[-1].get("content", "")
                store_provider_context(session_id, last_user_message, response.content)
            except Exception as exc:
                logger.warning("provider_context_storage_failed", error=str(exc))

        await self._record_cost(
            db,
            response.usage,
            organization_id=user.organization_id,
            user_id=user.id,
            provider_id=provider.id,
        )
        return response

    async def execute_with_fallback(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        messages: list[dict[str, str]],
        model: str | None = None,
        preferred_provider_id: int | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        response_format: dict[str, str] | None = None,
    ) -> ProviderResponse:
        """Execute an AI request with provider fallback chain."""
        providers = await provider_repository.get_active_by_organization(db, organization_id)
        if preferred_provider_id:
            providers = sorted(
                providers,
                key=lambda p: (p.id != preferred_provider_id, p.fallback_order),
            )

        if not providers:
            raise AppException("No active AI providers configured", status_code=400)

        last_error: Exception | None = None
        for provider in providers:
            config = self._build_runtime_config(provider)
            try:
                adapter = ProviderRegistry.create(provider.provider_type, config)
                selected_model = model or (provider.models[0].external_id if provider.models else "")
                if not selected_model:
                    continue
                response = await adapter.chat_completion(
                    messages=messages,
                    model=selected_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
                await self._record_cost(
                    db,
                    response.usage,
                    organization_id=organization_id,
                    provider_id=provider.id,
                )
                return response
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "provider_request_failed",
                    provider_id=provider.id,
                    error=str(exc),
                )
                continue

        raise AppException(
            f"All providers failed: {last_error}",
            status_code=502,
        ) from last_error

    def _build_runtime_config(
        self, provider: Provider, *, override_key: str | None = None
    ) -> dict[str, Any]:
        """Build runtime configuration for a provider adapter."""
        config = (provider.config or {}).copy()
        config["provider_type"] = provider.provider_type
        if override_key:
            config[PROVIDER_API_KEY_FIELDS.get(provider.provider_type, "api_key")] = override_key
        elif provider.api_key_encrypted:
            api_key = decrypt(provider.api_key_encrypted)
            config[PROVIDER_API_KEY_FIELDS.get(provider.provider_type, "api_key")] = api_key
        if provider.api_base:
            config["api_base"] = provider.api_base
        if provider.api_version:
            config["api_version"] = provider.api_version
        if provider.region:
            config["region"] = provider.region
        return config

    async def _record_cost(
        self,
        db: AsyncSession,
        usage: Any,
        *,
        organization_id: int,
        user_id: int | None,
        provider_id: int,
    ) -> None:
        """Record AI usage cost in the ledger."""
        from app.crud.base import BaseRepository

        ledger_repo = BaseRepository(CostLedger)
        await ledger_repo.create(
            db,
            obj_in={
                "provider_type": usage.provider_type,
                "model": usage.model,
                "operation": "chat_completion",
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
                "cost": usage.cost,
                "currency": "USD",
                "organization_id": organization_id,
                "user_id": user_id,
                "provider_id": provider_id,
            },
        )
        await db.commit()


provider_service = ProviderService()
