"""Chat session Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageCreate(BaseModel):
    """Payload to create a chat message."""

    role: str = Field(..., max_length=20)
    content: str = Field(..., max_length=20000)


class ChatMessageInDB(ChatMessageCreate):
    """Chat message database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    model: str | None
    input_tokens: int
    output_tokens: int
    cost: float
    created_at: datetime


class ChatSessionCreate(BaseModel):
    """Payload to create a chat session."""

    title: str | None = Field(None, max_length=255)
    topic_id: int


class ChatSessionUpdate(BaseModel):
    """Payload to update a chat session."""

    title: str | None = Field(None, max_length=255)
    is_active: bool | None = None


class ChatSessionInDB(BaseModel):
    """Chat session database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None
    is_active: bool
    topic_id: int
    user_id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime


class ChatSessionPublic(ChatSessionInDB):
    """Public chat session with messages."""

    messages: list[ChatMessageInDB]
