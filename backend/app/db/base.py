"""SQLAlchemy declarative base and audit mixin."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Integer, String, event
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


def now_utc() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Declarative base for all models."""

    type_annotation_map: dict[type[Any], Any] = {
        datetime: DateTime(timezone=True),
    }

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table names automatically from class names."""
        return "".join(["_" + c.lower() if c.isupper() else c for c in cls.__name__]).lstrip("_")


class AuditMixin:
    """Mixin adding audit and soft-delete fields."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    @property
    def is_deleted(self) -> bool:
        """Return True if the record has been soft-deleted."""
        return self.deleted_at is not None


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


@event.listens_for(Base, "before_update", propagate=True)
def receive_before_update(mapper: Any, connection: Any, target: Any) -> None:
    """Automatically update updated_at on every update."""
    if hasattr(target, "updated_at"):
        target.updated_at = now_utc()
