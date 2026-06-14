"""Chat session endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, status

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep, require_permissions
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.topic import topic_repository
from app.models.user import User
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageInDB,
    ChatSessionCreate,
    ChatSessionPublic,
    ChatSessionUpdate,
)
from app.services.chat_service import chat_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("/sessions", response_model=list[ChatSessionPublic])
async def list_sessions(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    topic_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List chat sessions for the organization or topic."""
    from app.crud.base import BaseRepository
    from app.models.chat import ChatSession
    from sqlalchemy import select

    stmt = select(ChatSession).where(
        ChatSession.organization_id == org_id,
        ChatSession.deleted_at.is_(None),
    )
    if topic_id:
        stmt = stmt.where(ChatSession.topic_id == topic_id)
    stmt = stmt.order_by(ChatSession.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/sessions", response_model=ChatSessionPublic, status_code=status.HTTP_201_CREATED)
async def create_session(
    db: DbDep,
    org_id: OrgIdDep,
    obj_in: ChatSessionCreate,
    current_user: User = Depends(require_permissions("topics:write")),
) -> Any:
    """Create a new chat session for a topic."""
    session = await chat_service.create_session(db, obj_in=obj_in, user=current_user)
    return session


@router.get("/sessions/{session_id}", response_model=ChatSessionPublic)
async def get_session(
    db: DbDep,
    org_id: OrgIdDep,
    session_id: int,
    current_user: ActiveUserDep,
) -> Any:
    """Get a chat session with messages."""
    from app.crud.base import BaseRepository
    from app.models.chat import ChatSession

    repo = BaseRepository(ChatSession)
    session = await repo.get_or_404(db, session_id)
    if session.organization_id != org_id:
        raise ForbiddenException("Access denied")
    return session


@router.put("/sessions/{session_id}", response_model=ChatSessionPublic)
async def update_session(
    db: DbDep,
    org_id: OrgIdDep,
    session_id: int,
    obj_in: ChatSessionUpdate,
    current_user: ActiveUserDep,
) -> Any:
    """Update a chat session."""
    from app.crud.base import BaseRepository
    from app.models.chat import ChatSession

    repo = BaseRepository(ChatSession)
    session = await repo.get_or_404(db, session_id)
    if session.organization_id != org_id:
        raise ForbiddenException("Access denied")
    session = await repo.update(
        db, db_obj=session, obj_in=obj_in.model_dump(exclude_unset=True)
    )
    await db.commit()
    await db.refresh(session)
    return session


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageInDB)
async def add_message(
    db: DbDep,
    org_id: OrgIdDep,
    session_id: int,
    obj_in: ChatMessageCreate,
    current_user: User = Depends(require_permissions("topics:write")),
) -> Any:
    """Add a user message to a session and generate an AI reply."""
    from app.crud.base import BaseRepository
    from app.models.chat import ChatSession

    repo = BaseRepository(ChatSession)
    session = await repo.get_or_404(db, session_id)
    if session.organization_id != org_id:
        raise ForbiddenException("Access denied")

    await chat_service.add_message(
        db, session=session, obj_in=obj_in, user=current_user
    )
    assistant_message = await chat_service.generate_reply(
        db, session=session, user=current_user
    )
    return assistant_message
