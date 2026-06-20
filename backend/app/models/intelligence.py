"""Intelligence ingestion and newsfeed models."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditMixin, Base


class IntelligenceSource(Base, AuditMixin):
    """Configured external or internal source for intelligence ingestion."""

    __tablename__ = "intelligence_sources"

    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    query: Mapped[str | None] = mapped_column(Text, nullable=True)
    configuration: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    refresh_interval_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    fetch_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    competitor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("competitors.id", ondelete="SET NULL"), nullable=True, index=True
    )
    topic_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True
    )

    items: Mapped[list["IntelligenceItem"]] = relationship(
        "IntelligenceItem",
        back_populates="source",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class IntelligenceItem(Base, AuditMixin):
    """A single piece of ingested intelligence, curated and enriched for the newsfeed."""

    __tablename__ = "intelligence_items"

    item_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    entities: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_noise: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("intelligence_sources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    competitor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("competitors.id", ondelete="SET NULL"), nullable=True, index=True
    )
    topic_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True
    )

    source: Mapped["IntelligenceSource"] = relationship("IntelligenceSource", back_populates="items")
