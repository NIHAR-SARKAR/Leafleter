"""Topic workspace and analysis models."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditMixin, Base


class Topic(Base, AuditMixin):
    """Research topic workspace for an organization."""

    __tablename__ = "topics"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    configuration: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    sources: Mapped[list["TopicSource"]] = relationship(
        "TopicSource", back_populates="topic", lazy="selectin", cascade="all, delete-orphan"
    )
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(
        "AnalysisRun", back_populates="topic", lazy="selectin"
    )
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="topic", lazy="selectin")


class TopicSource(Base, AuditMixin):
    """Data source attached to a topic."""

    __tablename__ = "topic_sources"

    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    query: Mapped[str | None] = mapped_column(Text, nullable=True)
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True)
    account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    configuration: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetch_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    fetch_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    topic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
    )

    topic: Mapped["Topic"] = relationship("Topic", back_populates="sources")


class AnalysisRun(Base, AuditMixin):
    """Execution record for an analysis job."""

    __tablename__ = "analysis_runs"

    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    configuration: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    topic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("providers.id", ondelete="SET NULL"), nullable=True
    )

    topic: Mapped["Topic"] = relationship("Topic", back_populates="analysis_runs")
    results: Mapped[list["AnalysisResult"]] = relationship(
        "AnalysisResult", back_populates="run", lazy="selectin", cascade="all, delete-orphan"
    )


class AnalysisResult(Base, AuditMixin):
    """Result payload from an analysis run."""

    __tablename__ = "analysis_results"

    result_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    score: Mapped[float | None] = mapped_column(nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="results")
