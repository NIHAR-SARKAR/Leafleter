"""Alert rule endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Response, status

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep, require_permissions
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.alert import AlertRule
from app.models.user import User
from app.schemas.alert import AlertRuleCreate, AlertRuleInDB, AlertRuleUpdate
from app.services.alert_service import alert_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=list[AlertRuleInDB])
async def list_alert_rules(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List alert rules for the organization."""
    repo = BaseRepository(AlertRule)
    rules = await repo.get_multi(db, organization_id=org_id, skip=skip, limit=limit)
    return rules


@router.post("", response_model=AlertRuleInDB, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    db: DbDep,
    org_id: OrgIdDep,
    obj_in: AlertRuleCreate,
    current_user: User = Depends(require_permissions("alerts:write")),
) -> Any:
    """Create a new alert rule."""
    rule = await alert_service.create_rule(db, obj_in=obj_in, user=current_user)
    return rule


@router.get("/{rule_id}", response_model=AlertRuleInDB)
async def get_alert_rule(
    db: DbDep,
    org_id: OrgIdDep,
    rule_id: int,
    current_user: ActiveUserDep,
) -> Any:
    """Get a specific alert rule."""
    repo = BaseRepository(AlertRule)
    rule = await repo.get_or_404(db, rule_id)
    if rule.organization_id != org_id:
        raise ForbiddenException("Access denied")
    return rule


@router.put("/{rule_id}", response_model=AlertRuleInDB)
async def update_alert_rule(
    db: DbDep,
    org_id: OrgIdDep,
    rule_id: int,
    obj_in: AlertRuleUpdate,
    current_user: User = Depends(require_permissions("alerts:write")),
) -> Any:
    """Update an alert rule."""
    repo = BaseRepository(AlertRule)
    rule = await repo.get_or_404(db, rule_id)
    if rule.organization_id != org_id:
        raise ForbiddenException("Access denied")
    rule = await alert_service.update_rule(db, rule=rule, obj_in=obj_in)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    db: DbDep,
    org_id: OrgIdDep,
    rule_id: int,
    current_user: User = Depends(require_permissions("alerts:write")),
) -> None:
    """Delete an alert rule."""
    repo = BaseRepository(AlertRule)
    rule = await repo.get_or_404(db, rule_id)
    if rule.organization_id != org_id:
        raise ForbiddenException("Access denied")
    await alert_service.delete_rule(db, rule=rule)
    return None
