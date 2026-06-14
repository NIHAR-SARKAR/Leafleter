"""API key endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Response, status

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep, require_permissions
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.api_key import api_key_repository
from app.models.user import User
from app.schemas.api_key import APIKeyCreate, APIKeyPublic, APIKeyUpdate

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=list[APIKeyPublic])
async def list_api_keys(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List API keys for the current organization."""
    keys = await api_key_repository.get_multi(
        db, organization_id=org_id, skip=skip, limit=limit
    )
    return keys


@router.post("", response_model=APIKeyPublic, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    db: DbDep,
    org_id: OrgIdDep,
    obj_in: APIKeyCreate,
    current_user: User = Depends(require_permissions("settings:write")),
) -> Any:
    """Create a new API key."""
    from app.services.auth_service import auth_service

    api_key, plain_key = await auth_service.create_api_key(
        db, obj_in=obj_in, user=current_user
    )
    return {
        **APIKeyPublic.model_validate(api_key).model_dump(),
        "plain_key": plain_key,
    }


@router.get("/{api_key_id}", response_model=APIKeyPublic)
async def get_api_key(
    db: DbDep,
    org_id: OrgIdDep,
    api_key_id: int,
    current_user: ActiveUserDep,
) -> Any:
    """Get a specific API key."""
    key = await api_key_repository.get_or_404(db, api_key_id)
    if key.organization_id != org_id:
        raise ForbiddenException("Access denied")
    return key


@router.put("/{api_key_id}", response_model=APIKeyPublic)
async def update_api_key(
    db: DbDep,
    org_id: OrgIdDep,
    api_key_id: int,
    obj_in: APIKeyUpdate,
    current_user: User = Depends(require_permissions("settings:write")),
) -> Any:
    """Update an API key."""
    key = await api_key_repository.get_or_404(db, api_key_id)
    if key.organization_id != org_id:
        raise ForbiddenException("Access denied")
    update_data = obj_in.model_dump(exclude_unset=True)
    if "scopes" in update_data and update_data["scopes"] is not None:
        update_data["scopes"] = ",".join(update_data["scopes"])
    key = await api_key_repository.update(db, db_obj=key, obj_in=update_data)
    await db.commit()
    await db.refresh(key)
    return key


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    db: DbDep,
    org_id: OrgIdDep,
    api_key_id: int,
    current_user: User = Depends(require_permissions("settings:write")),
) -> None:
    """Delete an API key."""
    key = await api_key_repository.get_or_404(db, api_key_id)
    if key.organization_id != org_id:
        raise ForbiddenException("Access denied")
    await api_key_repository.delete(db, db_obj=key)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
