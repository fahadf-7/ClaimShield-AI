from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common import IdMixin, TimestampMixin
from app.database import Base
from app.enums import JobState


class AnalysisJob(IdMixin, TimestampMixin, Base):
    __tablename__ = "analysis_jobs"

    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    inspection_id: Mapped[str] = mapped_column(ForeignKey("inspections.id"), index=True)
    claim_id: Mapped[str | None] = mapped_column(ForeignKey("claims.id"), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(80), default="FOUNDATION_VALIDATION")
    state: Mapped[str] = mapped_column(String(20), default=JobState.QUEUED.value)
    progress: Mapped[int] = mapped_column(default=0)
    attempt_count: Mapped[int] = mapped_column(default=0)
    correlation_id: Mapped[str] = mapped_column(String(36), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(120), index=True)
    error_category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

