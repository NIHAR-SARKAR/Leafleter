"""Report comment Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserShort


class ReportCommentCreate(BaseModel):
    """Report comment creation payload."""

    content: str = Field(..., max_length=5000)


class ReportCommentInDB(BaseModel):
    """Report comment database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    report_id: int
    user_id: int
    user: UserShort | None = None
    organization_id: int
    created_at: datetime
