"""Fact extraction and insight models for the Intelligence Core."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditMixin, Base, now_utc


class FactTemplate(Base, AuditMixin):
    """Template that defines how to extract a structured fact from intelligence."""

    __tablename__ = "fact_templates"

    fact_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    schema_definition: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    example: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )

    facts: Mapped[list["Fact"]] = relationship(
        "Fact", back_populates="template", lazy="selectin"
    )


class Fact(Base):
    """A structured fact extracted from one or more intelligence items."""

    __tablename__ = "facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    fact_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    evidence: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    effective_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fact_templates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    competitor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("competitors.id", ondelete="SET NULL"), nullable=True, index=True
    )
    item_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("intelligence_items.id", ondelete="SET NULL"), nullable=True, index=True
    )

    template: Mapped["FactTemplate"] = relationship("FactTemplate", back_populates="facts")
