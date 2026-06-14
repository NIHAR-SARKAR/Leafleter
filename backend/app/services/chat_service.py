"""Chat service for topic workspaces."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.logging import get_logger
from app.crud.provider import provider_repository
from app.crud.topic import topic_repository
from app.models.chat import ChatMessage, ChatSession
from app.models.topic import Topic
from app.models.user import User
from app.providers.base import ProviderUsage
from app.providers.registry import ProviderRegistry
from app.schemas.chat import ChatMessageCreate, ChatSessionCreate
from app.services.provider_service import provider_service

logger = get_logger(__name__)


class ChatService:
    """Service for managing topic chat sessions and AI replies."""

    async def create_session(
        self,
        db: AsyncSession,
        *,
        obj_in: ChatSessionCreate,
        user: User,
    ) -> ChatSession:
        """Create a new chat session for a topic."""
        topic = await topic_repository.get_or_404_for_organization(
            db, obj_in.topic_id, user.organization_id
        )
        session = await self._create_session(db, obj_in=obj_in, user=user, topic=topic)
        await db.commit()
        await db.refresh(session)
        logger.info(
            "chat_session_created",
            session_id=session.id,
            topic_id=topic.id,
            user_id=user.id,
        )
        return session

    async def _create_session(
        self,
        db: AsyncSession,
        *,
        obj_in: ChatSessionCreate,
        user: User,
        topic: Topic,
    ) -> ChatSession:
        """Internal helper to create a chat session."""
        from app.crud.base import BaseRepository

        repo = BaseRepository(ChatSession)
        return await repo.create(
            db,
            obj_in={
                "title": obj_in.title or f"Chat about {topic.name}",
                "topic_id": topic.id,
                "user_id": user.id,
                "organization_id": user.organization_id,
                "is_active": True,
            },
        )

    async def add_message(
        self,
        db: AsyncSession,
        *,
        session: ChatSession,
        obj_in: ChatMessageCreate,
        user: User,
    ) -> ChatMessage:
        """Add a message to a session."""
        if session.organization_id != user.organization_id:
            raise ForbiddenException("Access denied")

        from app.crud.base import BaseRepository

        repo = BaseRepository(ChatMessage)
        message = await repo.create(
            db,
            obj_in={
                "session_id": session.id,
                "role": obj_in.role,
                "content": obj_in.content,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0,
            },
        )
        await db.commit()
        await db.refresh(message)
        return message

    async def generate_reply(
        self,
        db: AsyncSession,
        *,
        session: ChatSession,
        user: User,
        provider_id: int | None = None,
        model: str | None = None,
    ) -> ChatMessage:
        """Generate an AI assistant reply for the current session."""
        if session.organization_id != user.organization_id:
            raise ForbiddenException("Access denied")

        provider = await self._resolve_provider(db, user, provider_id)
        config = provider_service._build_runtime_config(provider)
        adapter = ProviderRegistry.create(provider.provider_type, config)
        selected_model = model or (
            provider.models[0].external_id if provider.models else ""
        )
        if not selected_model:
            raise NotFoundException("No model available")

        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in session.messages
        ]
        messages.append(
            {
                "role": "system",
                "content": "You are a market intelligence assistant. Answer based on the topic data.",
            }
        )

        response = await adapter.chat_completion(
            messages=messages,
            model=selected_model,
            temperature=0.7,
            max_tokens=2000,
        )

        from app.crud.base import BaseRepository

        repo = BaseRepository(ChatMessage)
        assistant_message = await repo.create(
            db,
            obj_in={
                "session_id": session.id,
                "role": "assistant",
                "content": response.content,
                "model": selected_model,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cost": response.usage.cost,
            },
        )
        await provider_service._record_cost(
            db,
            response.usage,
            organization_id=user.organization_id,
            user_id=user.id,
            provider_id=provider.id,
        )
        await db.commit()
        await db.refresh(assistant_message)
        return assistant_message

    async def _resolve_provider(
        self,
        db: AsyncSession,
        user: User,
        provider_id: int | None,
    ) -> Any:
        """Resolve provider for chat."""
        if provider_id:
            provider = await provider_repository.get(db, provider_id)
            if provider is None or provider.organization_id != user.organization_id:
                raise NotFoundException("Provider not found")
            return provider
        provider = await provider_repository.get_default_for_organization(
            db, user.organization_id
        )
        if provider is None:
            raise NotFoundException("No active AI provider configured")
        return provider


chat_service = ChatService()
