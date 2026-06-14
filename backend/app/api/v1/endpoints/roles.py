"""Role and permission endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Response, status

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep, require_permissions
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.role import permission_repository, role_repository
from app.models.user import User
from app.schemas.role import PermissionInDB, RoleCreate, RolePublic, RoleUpdate

logger = get_logger(__name__)
router = APIRouter()


@router.get("/permissions", response_model=list[PermissionInDB])
async def list_permissions(
    db: DbDep,
    current_user: ActiveUserDep,
    skip: int = 0,
    limit: int = 200,
) -> Any:
    """List all available permissions."""
    perms = await permission_repository.get_multi(db, skip=skip, limit=limit)
    return perms


@router.get("", response_model=list[RolePublic])
async def list_roles(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List roles for the current organization."""
    roles = await role_repository.get_multi(
        db, organization_id=org_id, skip=skip, limit=limit
    )
    return roles


@router.post("", response_model=RolePublic, status_code=status.HTTP_201_CREATED)
async def create_role(
    db: DbDep,
    org_id: OrgIdDep,
    obj_in: RoleCreate,
    current_user: User = Depends(require_permissions("users:write")),
) -> Any:
    """Create a custom role for the organization."""
    permissions = []
    for perm_id in obj_in.permission_ids:
        perm = await permission_repository.get(db, perm_id)
        if perm is None:
            raise ForbiddenException("Permission not found")
        permissions.append(perm)

    role = await role_repository.create(
        db,
        obj_in={
            "name": obj_in.name,
            "description": obj_in.description,
            "is_system": False,
            "organization_id": org_id,
        },
    )
    role.permissions = permissions
    db.add(role)
    await db.commit()
    await db.refresh(role)
    logger.info("role_created", role_id=role.id, organization_id=org_id)
    return role


@router.get("/{role_id}", response_model=RolePublic)
async def get_role(
    db: DbDep,
    org_id: OrgIdDep,
    role_id: int,
    current_user: ActiveUserDep,
) -> Any:
    """Get a specific role."""
    role = await role_repository.get_or_404(db, role_id)
    if role.organization_id != org_id:
        raise ForbiddenException("Access denied")
    return role


@router.put("/{role_id}", response_model=RolePublic)
async def update_role(
    db: DbDep,
    org_id: OrgIdDep,
    role_id: int,
    obj_in: RoleUpdate,
    current_user: User = Depends(require_permissions("users:write")),
) -> Any:
    """Update a custom role."""
    role = await role_repository.get_or_404(db, role_id)
    if role.organization_id != org_id:
        raise ForbiddenException("Access denied")
    if role.is_system:
        raise ForbiddenException("Cannot modify system roles")

    update_data = obj_in.model_dump(exclude_unset=True)
    permission_ids = update_data.pop("permission_ids", None)
    if permission_ids is not None:
        permissions = []
        for perm_id in permission_ids:
            perm = await permission_repository.get(db, perm_id)
            if perm is None:
                raise ForbiddenException("Permission not found")
            permissions.append(perm)
        role.permissions = permissions

    role = await role_repository.update(db, db_obj=role, obj_in=update_data)
    await db.commit()
    await db.refresh(role)
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    db: DbDep,
    org_id: OrgIdDep,
    role_id: int,
    current_user: User = Depends(require_permissions("users:write")),
) -> None:
    """Delete a custom role."""
    role = await role_repository.get_or_404(db, role_id)
    if role.organization_id != org_id:
        raise ForbiddenException("Access denied")
    if role.is_system:
        raise ForbiddenException("Cannot delete system roles")
    await role_repository.delete(db, db_obj=role)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
