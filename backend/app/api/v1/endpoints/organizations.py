"""Organization endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, status

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep, require_permissions
from app.models.user import User
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.organization import organization_repository
from app.schemas.organization import (
    OrganizationBranding,
    OrganizationInDB,
    OrganizationUpdate,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/me", response_model=OrganizationInDB)
async def get_current_organization(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
) -> Any:
    """Return the current user's organization."""
    org = await organization_repository.get_or_404(db, org_id)
    return org


@router.put("/me", response_model=OrganizationInDB)
async def update_current_organization(
    db: DbDep,
    org_id: OrgIdDep,
    obj_in: OrganizationUpdate,
    current_user: User = Depends(require_permissions("settings:write")),
) -> Any:
    """Update the current organization."""
    org = await organization_repository.get_or_404(db, org_id)
    update_data = obj_in.model_dump(exclude_unset=True)
    org = await organization_repository.update(db, db_obj=org, obj_in=update_data)
    logger.info("organization_updated", organization_id=org_id, user_id=current_user.id)
    return org


@router.put("/me/branding", response_model=OrganizationInDB)
async def update_organization_branding(
    db: DbDep,
    org_id: OrgIdDep,
    obj_in: OrganizationBranding,
    current_user: User = Depends(require_permissions("settings:write")),
) -> Any:
    """Update white-label branding for the organization."""
    org = await organization_repository.get_or_404(db, org_id)
    if not org.is_white_label and not current_user.is_superuser:
        raise ForbiddenException("White label is not enabled for this organization")
    update_data = obj_in.model_dump(exclude_unset=True)
    org = await organization_repository.update(db, db_obj=org, obj_in=update_data)
    logger.info("organization_branding_updated", organization_id=org_id)
    return org
