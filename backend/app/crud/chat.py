"""Chat session and message repositories."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.chat import ChatMessage, ChatSession

logger = get_logger(__name__)


class ChatSessionRepository(BaseRepository[ChatSession]):
    """Repository for chat sessions."""

    def __init__(self) -> None:
        super().__init__(ChatSession)

    async def get_by_user_and_organization(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ChatSession]:
        """List chat sessions for a user within an organization."""
        result = await db.execute(
            select(ChatSession)
            .where(
                ChatSession.user_id == user_id,
                ChatSession.organization_id == organization_id,
                ChatSession.deleted_at.is_(None),
            )
            .order_by(ChatSession.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


class ChatMessageRepository(BaseRepository[ChatMessage]):
    """Repository for chat messages."""

    def __init__(self) -> None:
        super().__init__(ChatMessage)

    async def get_by_session(
        self,
        db: AsyncSession,
        session_id: int,
        skip: int = 0,
        limit: int = 500,
    ) -> Sequence[ChatMessage]:
        """List messages in a chat session ordered by creation time."""
        result = await db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.deleted_at.is_(None),
            )
            .order_by(ChatMessage.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


# Global repository instances.
chat_session_repository = ChatSessionRepository()
chat_message_repository = ChatMessageRepository()
