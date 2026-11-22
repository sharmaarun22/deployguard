from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db import Base


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    repository: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="unknown")
    source: Mapped[str] = mapped_column(Text, nullable=False)
    findings: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class PipelineExecution(Base):
    __tablename__ = "pipeline_executions"
    __table_args__ = (
        UniqueConstraint(
            "pipeline_id", "external_id", name="uq_pipeline_executions_pipeline_external"
        ),
        CheckConstraint(
            "status IN ('success', 'failure', 'cancelled', 'unknown')",
            name="ck_pipeline_executions_status",
        ),
        Index("ix_pipeline_executions_pipeline_created", "pipeline_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_id: Mapped[int] = mapped_column(
        ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    classification: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class TestExecution(Base):
    __tablename__ = "test_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_format: Mapped[str] = mapped_column(String(30), nullable=False)
    suite: Mapped[str] = mapped_column(String(200), nullable=False)
    test_name: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, default=0)
    failure_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class InfrastructureFinding(Base):
    __tablename__ = "infrastructure_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    resource: Mapped[str] = mapped_column(String(500), nullable=False)
    rule: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class NotificationRule(Base):
    __tablename__ = "notification_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    minimum_severity: Mapped[str] = mapped_column(String(30), default="medium")
    webhook_url: Mapped[str | None] = mapped_column(String(2000))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
