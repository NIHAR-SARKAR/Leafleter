"""Notification endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Response, status

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep, require_permissions
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationCreate, NotificationInDB, NotificationUpdate
from app.services.notification_service import notification_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=list[NotificationInDB])
async def list_notifications(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List notifications for the organization."""
    repo = BaseRepository(Notification)
    notifications = await repo.get_multi(
        db, organization_id=org_id, skip=skip, limit=limit
    )
    return notifications


@router.post("", response_model=NotificationInDB, status_code=status.HTTP_201_CREATED)
async def create_notification(
    db: DbDep,
    org_id: OrgIdDep,
    obj_in: NotificationCreate,
    current_user: User = Depends(require_permissions("alerts:write")),
) -> Any:
    """Create and send a notification."""
    notification = await notification_service.send_notification(
        db, obj_in=obj_in, organization_id=org_id, user_id=current_user.id
    )
    return notification


@router.put("/{notification_id}", response_model=NotificationInDB)
async def update_notification(
    db: DbDep,
    org_id: OrgIdDep,
    notification_id: int,
    obj_in: NotificationUpdate,
    current_user: ActiveUserDep,
) -> Any:
    """Mark a notification as read."""
    repo = BaseRepository(Notification)
    notification = await repo.get_or_404(db, notification_id)
    if notification.organization_id != org_id:
        raise ForbiddenException("Access denied")
    notification = await repo.update(
        db, db_obj=notification, obj_in=obj_in.model_dump(exclude_unset=True)
    )
    await db.commit()
    await db.refresh(notification)
    return notification
