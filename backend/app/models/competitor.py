"""Competitor and snapshot models."""

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditMixin, Base


class Competitor(Base, AuditMixin):
    """Competitor tracked by an organization."""

    __tablename__ = "competitors"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    social_handles: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    watch_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    snapshots: Mapped[list["CompetitorSnapshot"]] = relationship(
        "CompetitorSnapshot",
        back_populates="competitor",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class CompetitorSnapshot(Base, AuditMixin):
    """Point-in-time snapshot of competitor data."""

    __tablename__ = "competitor_snapshots"

    snapshot_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    changes: Mapped[str | None] = mapped_column(Text, nullable=True)
    competitor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False, index=True
    )

    competitor: Mapped["Competitor"] = relationship("Competitor", back_populates="snapshots")
