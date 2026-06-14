"""AI provider management endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, status

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep, require_permissions
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.provider import provider_repository
from app.models.user import User
from app.providers.registry import ProviderRegistry
from app.schemas.provider import (
    ProviderChatRequest,
    ProviderCreate,
    ProviderInDB,
    ProviderPublic,
    ProviderTestRequest,
    ProviderTestResponse,
    ProviderUpdate,
)
from app.services.provider_service import provider_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("/types", response_model=list[str])
async def list_provider_types(
    current_user: ActiveUserDep,
) -> Any:
    """Return supported AI provider types."""
    return ProviderRegistry.supported()


@router.get("", response_model=list[ProviderInDB])
async def list_providers(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List AI providers for the organization."""
    providers = await provider_repository.get_active_by_organization(
        db, org_id, skip=skip, limit=limit
    )
    return providers


@router.post("", response_model=ProviderPublic, status_code=status.HTTP_201_CREATED)
async def create_provider(
    db: DbDep,
    org_id: OrgIdDep,
    obj_in: ProviderCreate,
    current_user: User = Depends(require_permissions("providers:write")),
) -> Any:
    """Create a new AI provider configuration."""
    provider = await provider_service.create(
        db, obj_in=obj_in, organization_id=org_id, created_by=current_user
    )
    return provider


@router.get("/{provider_id}", response_model=ProviderPublic)
async def get_provider(
    db: DbDep,
    org_id: OrgIdDep,
    provider_id: int,
    current_user: ActiveUserDep,
) -> Any:
    """Get a specific provider configuration."""
    provider = await provider_repository.get_or_404(db, provider_id)
    if provider.organization_id != org_id:
        raise ForbiddenException("Access denied")
    return provider


@router.put("/{provider_id}", response_model=ProviderPublic)
async def update_provider(
    db: DbDep,
    org_id: OrgIdDep,
    provider_id: int,
    obj_in: ProviderUpdate,
    current_user: User = Depends(require_permissions("providers:write")),
) -> Any:
    """Update an AI provider configuration."""
    provider = await provider_repository.get_or_404(db, provider_id)
    if provider.organization_id != org_id:
        raise ForbiddenException("Access denied")
    provider = await provider_service.update(db, provider=provider, obj_in=obj_in)
    return provider


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    db: DbDep,
    org_id: OrgIdDep,
    provider_id: int,
    current_user: User = Depends(require_permissions("providers:write")),
) -> None:
    """Soft delete an AI provider configuration."""
    provider = await provider_repository.get_or_404(db, provider_id)
    if provider.organization_id != org_id:
        raise ForbiddenException("Access denied")
    await provider_service.delete(db, provider=provider)
    return None


@router.post("/{provider_id}/test", response_model=ProviderTestResponse)
async def test_provider(
    db: DbDep,
    org_id: OrgIdDep,
    provider_id: int,
    obj_in: ProviderTestRequest | None = None,
    current_user: User = Depends(require_permissions("providers:write")),
) -> Any:
    """Test an AI provider connection."""
    provider = await provider_repository.get_or_404(db, provider_id)
    if provider.organization_id != org_id:
        raise ForbiddenException("Access denied")
    result = await provider_service.test_connection(
        db,
        provider=provider,
        api_key=obj_in.api_key if obj_in else None,
    )
    return result


@router.post("/{provider_id}/chat", response_model=dict[str, Any])
async def chat_with_provider(
    db: DbDep,
    org_id: OrgIdDep,
    provider_id: int,
    obj_in: ProviderChatRequest,
    current_user: User = Depends(require_permissions("providers:write")),
) -> Any:
    """Send a chat completion request directly through a provider."""
    provider = await provider_repository.get_or_404(db, provider_id)
    if provider.organization_id != org_id:
        raise ForbiddenException("Access denied")
    response = await provider_service.chat(
        db, provider=provider, obj_in=obj_in, user=current_user
    )
    return {
        "content": response.content,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.total_tokens,
            "cost": response.usage.cost,
            "model": response.usage.model,
        },
        "finish_reason": response.finish_reason,
    }
