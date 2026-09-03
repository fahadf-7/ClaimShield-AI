from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.common import IdMixin, TimestampMixin
from app.database import Base
from app.enums import AnalysisState


class ModelVersion(IdMixin, TimestampMixin, Base):
    __tablename__ = "model_versions"
    __table_args__ = (UniqueConstraint("task", "name", "version", name="uq_model_task_name_version"),)

    task: Mapped[str] = mapped_column(String(40), index=True)
    name: Mapped[str] = mapped_column(String(120))
    version: Mapped[str] = mapped_column(String(80))
    adapter: Mapped[str] = mapped_column(String(40))
    weights_checksum: Mapped[str] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(500))
    license: Mapped[str] = mapped_column(String(120))
    preprocessing_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    thresholds_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    class_mapping_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_experimental: Mapped[bool] = mapped_column(Boolean, default=True)


class AnalysisRun(IdMixin, TimestampMixin, Base):
    __tablename__ = "analysis_runs"
    __table_args__ = (UniqueConstraint("inspection_id", "version", name="uq_analysis_inspection_version"),)

    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    inspection_id: Mapped[str] = mapped_column(ForeignKey("inspections.id"), index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("analysis_jobs.id"), nullable=True, index=True)
    version: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(20), default=AnalysisState.QUEUED.value)
    pipeline_version: Mapped[str] = mapped_column(String(80))
    threshold_version: Mapped[str] = mapped_column(String(80))
    part_model_version_id: Mapped[str | None] = mapped_column(ForeignKey("model_versions.id"), nullable=True)
    damage_model_version_id: Mapped[str | None] = mapped_column(ForeignKey("model_versions.id"), nullable=True)
    device: Mapped[str | None] = mapped_column(String(40), nullable=True)
    warnings_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    timings_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error_category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DerivedArtifact(IdMixin, TimestampMixin, Base):
    __tablename__ = "derived_artifacts"

    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    media_id: Mapped[str] = mapped_column(ForeignKey("media.id"), index=True)
    artifact_type: Mapped[str] = mapped_column(String(40), index=True)
    object_key: Mapped[str] = mapped_column(String(500), unique=True)
    content_type: Mapped[str] = mapped_column(String(80))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))


class VehiclePartDetection(IdMixin, TimestampMixin, Base):
    __tablename__ = "vehicle_part_detections"

    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    media_id: Mapped[str] = mapped_column(ForeignKey("media.id"), index=True)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"), index=True)
    class_name: Mapped[str] = mapped_column(String(40), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    mask_key: Mapped[str] = mapped_column(String(500), unique=True)
    mask_area: Mapped[int] = mapped_column(Integer)
    bbox_json: Mapped[list[int]] = mapped_column(JSON, default=list)
    raw_output_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class DamageDetection(IdMixin, TimestampMixin, Base):
    __tablename__ = "damage_detections"

    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    media_id: Mapped[str] = mapped_column(ForeignKey("media.id"), index=True)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"), index=True)
    vehicle_part_detection_id: Mapped[str | None] = mapped_column(
        ForeignKey("vehicle_part_detections.id"), nullable=True, index=True
    )
    class_name: Mapped[str] = mapped_column(String(40), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(20), default="UNKNOWN")
    coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    intersection_area: Mapped[int] = mapped_column(Integer, default=0)
    region_count: Mapped[int] = mapped_column(Integer, default=1)
    mask_key: Mapped[str] = mapped_column(String(500), unique=True)
    bbox_json: Mapped[list[int]] = mapped_column(JSON, default=list)
    raw_output_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class FindingCorrection(IdMixin, TimestampMixin, Base):
    __tablename__ = "finding_corrections"
    __table_args__ = (UniqueConstraint("finding_type", "finding_id", "version", name="uq_finding_correction_version"),)

    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    finding_type: Mapped[str] = mapped_column(String(20), index=True)
    finding_id: Mapped[str] = mapped_column(String(36), index=True)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(20))
    corrected_class: Mapped[str | None] = mapped_column(String(40), nullable=True)
    corrected_part_detection_id: Mapped[str | None] = mapped_column(
        ForeignKey("vehicle_part_detections.id"), nullable=True
    )
    corrected_severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer)
