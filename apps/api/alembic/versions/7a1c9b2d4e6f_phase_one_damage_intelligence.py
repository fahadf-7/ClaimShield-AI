"""phase one damage intelligence

Revision ID: 7a1c9b2d4e6f
Revises: f3fe57f1a5c8
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7a1c9b2d4e6f"
down_revision: str | None = "f3fe57f1a5c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_versions",
        sa.Column("task", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("version", sa.String(length=80), nullable=False),
        sa.Column("adapter", sa.String(length=40), nullable=False),
        sa.Column("weights_checksum", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=500), nullable=False),
        sa.Column("license", sa.String(length=120), nullable=False),
        sa.Column("preprocessing_json", sa.JSON(), nullable=False),
        sa.Column("thresholds_json", sa.JSON(), nullable=False),
        sa.Column("class_mapping_json", sa.JSON(), nullable=False),
        sa.Column("is_experimental", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task", "name", "version", name="uq_model_task_name_version"),
    )
    op.create_index(op.f("ix_model_versions_task"), "model_versions", ["task"], unique=False)
    op.create_table(
        "analysis_runs",
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("inspection_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("pipeline_version", sa.String(length=80), nullable=False),
        sa.Column("threshold_version", sa.String(length=80), nullable=False),
        sa.Column("part_model_version_id", sa.String(length=36), nullable=True),
        sa.Column("damage_model_version_id", sa.String(length=36), nullable=True),
        sa.Column("device", sa.String(length=40), nullable=True),
        sa.Column("warnings_json", sa.JSON(), nullable=False),
        sa.Column("timings_json", sa.JSON(), nullable=False),
        sa.Column("error_category", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["damage_model_version_id"], ["model_versions.id"]),
        sa.ForeignKeyConstraint(["inspection_id"], ["inspections.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["analysis_jobs.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["part_model_version_id"], ["model_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("inspection_id", "version", name="uq_analysis_inspection_version"),
    )
    for column in ("organization_id", "inspection_id", "job_id"):
        op.create_index(op.f(f"ix_analysis_runs_{column}"), "analysis_runs", [column], unique=False)
    op.create_table(
        "derived_artifacts",
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), nullable=False),
        sa.Column("media_id", sa.String(length=36), nullable=False),
        sa.Column("artifact_type", sa.String(length=40), nullable=False),
        sa.Column("object_key", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=80), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"]),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key"),
    )
    for column in ("organization_id", "analysis_run_id", "media_id", "artifact_type"):
        op.create_index(op.f(f"ix_derived_artifacts_{column}"), "derived_artifacts", [column], unique=False)
    op.create_table(
        "vehicle_part_detections",
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), nullable=False),
        sa.Column("media_id", sa.String(length=36), nullable=False),
        sa.Column("model_version_id", sa.String(length=36), nullable=False),
        sa.Column("class_name", sa.String(length=40), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("mask_key", sa.String(length=500), nullable=False),
        sa.Column("mask_area", sa.Integer(), nullable=False),
        sa.Column("bbox_json", sa.JSON(), nullable=False),
        sa.Column("raw_output_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"]),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"]),
        sa.ForeignKeyConstraint(["model_version_id"], ["model_versions.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mask_key"),
    )
    for column in ("organization_id", "analysis_run_id", "media_id", "model_version_id", "class_name"):
        op.create_index(op.f(f"ix_vehicle_part_detections_{column}"), "vehicle_part_detections", [column], unique=False)
    op.create_table(
        "damage_detections",
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), nullable=False),
        sa.Column("media_id", sa.String(length=36), nullable=False),
        sa.Column("model_version_id", sa.String(length=36), nullable=False),
        sa.Column("vehicle_part_detection_id", sa.String(length=36), nullable=True),
        sa.Column("class_name", sa.String(length=40), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("coverage", sa.Float(), nullable=True),
        sa.Column("intersection_area", sa.Integer(), nullable=False),
        sa.Column("region_count", sa.Integer(), nullable=False),
        sa.Column("mask_key", sa.String(length=500), nullable=False),
        sa.Column("bbox_json", sa.JSON(), nullable=False),
        sa.Column("raw_output_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"]),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"]),
        sa.ForeignKeyConstraint(["model_version_id"], ["model_versions.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["vehicle_part_detection_id"], ["vehicle_part_detections.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mask_key"),
    )
    for column in ("organization_id", "analysis_run_id", "media_id", "model_version_id", "vehicle_part_detection_id", "class_name"):
        op.create_index(op.f(f"ix_damage_detections_{column}"), "damage_detections", [column], unique=False)
    op.create_table(
        "finding_corrections",
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), nullable=False),
        sa.Column("finding_type", sa.String(length=20), nullable=False),
        sa.Column("finding_id", sa.String(length=36), nullable=False),
        sa.Column("reviewer_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("corrected_class", sa.String(length=40), nullable=True),
        sa.Column("corrected_part_detection_id", sa.String(length=36), nullable=True),
        sa.Column("corrected_severity", sa.String(length=20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"]),
        sa.ForeignKeyConstraint(["corrected_part_detection_id"], ["vehicle_part_detections.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("finding_type", "finding_id", "version", name="uq_finding_correction_version"),
    )
    for column in ("organization_id", "analysis_run_id", "finding_type", "finding_id", "reviewer_id"):
        op.create_index(op.f(f"ix_finding_corrections_{column}"), "finding_corrections", [column], unique=False)


def downgrade() -> None:
    op.drop_table("finding_corrections")
    op.drop_table("damage_detections")
    op.drop_table("vehicle_part_detections")
    op.drop_table("derived_artifacts")
    op.drop_table("analysis_runs")
    op.drop_table("model_versions")
