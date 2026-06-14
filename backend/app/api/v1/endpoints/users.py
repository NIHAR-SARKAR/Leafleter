"""User management endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Response, status

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep, require_permissions
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.user import user_repository
from app.models.user import User
from app.schemas.user import UserCreate, UserPublic, UserUpdate
from app.services.user_service import user_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=list[UserPublic])
async def list_users(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List users in the current organization."""
    users = await user_repository.get_by_organization(db, org_id, skip=skip, limit=limit)
    return users


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user(
    db: DbDep,
    org_id: OrgIdDep,
    obj_in: UserCreate,
    current_user: User = Depends(require_permissions("users:write")),
) -> Any:
    """Create a new user in the organization."""
    user = await user_service.create(
        db, obj_in=obj_in, organization_id=org_id, created_by=current_user
    )
    return user


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    db: DbDep,
    org_id: OrgIdDep,
    user_id: int,
    current_user: ActiveUserDep,
) -> Any:
    """Get a specific user in the organization."""
    user = await user_repository.get_or_404(db, user_id)
    if user.organization_id != org_id:
        raise ForbiddenException("Access denied")
    return user


@router.put("/{user_id}", response_model=UserPublic)
async def update_user(
    db: DbDep,
    org_id: OrgIdDep,
    user_id: int,
    obj_in: UserUpdate,
    current_user: User = Depends(require_permissions("users:write")),
) -> Any:
    """Update a user in the organization."""
    user = await user_repository.get_or_404(db, user_id)
    if user.organization_id != org_id:
        raise ForbiddenException("Access denied")
    if user.id == current_user.id and obj_in.is_active is False:
        raise ForbiddenException("Cannot deactivate yourself")
    updated = await user_service.update(db, db_obj=user, obj_in=obj_in)
    return updated


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    db: DbDep,
    org_id: OrgIdDep,
    user_id: int,
    current_user: User = Depends(require_permissions("users:write")),
) -> None:
    """Soft delete a user in the organization."""
    user = await user_repository.get_or_404(db, user_id)
    if user.organization_id != org_id:
        raise ForbiddenException("Access denied")
    if user.id == current_user.id:
        raise ForbiddenException("Cannot delete yourself")
    await user_service.delete(db, user=user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
