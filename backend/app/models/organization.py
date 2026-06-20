"""Organization model representing a SaaS tenant."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditMixin, Base, generate_uuid, now_utc

if TYPE_CHECKING:
    from app.models.user import User


class Organization(Base, AuditMixin):
    """Organization (tenant) entity."""

    __tablename__ = "organizations"

    uuid: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=generate_uuid, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_white_label: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    billing_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    settings: Mapped[str | None] = mapped_column(Text, nullable=True)
    branding_primary_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    branding_logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    branding_favicon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    custom_domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    features: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)

    users: Mapped[list["User"]] = relationship(
        "User", back_populates="organization", lazy="selectin"
    )
