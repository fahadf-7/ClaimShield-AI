from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ModelVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task: str
    name: str
    version: str
    adapter: str
    weights_checksum: str
    source: str
    license: str
    preprocessing_json: dict[str, Any]
    thresholds_json: dict[str, Any]
    class_mapping_json: dict[str, Any]
    is_experimental: bool


class AnalysisRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    inspection_id: str
    job_id: str | None
    version: int
    state: str
    pipeline_version: str
    threshold_version: str
    device: str | None
    warnings_json: list[str]
    timings_json: dict[str, Any]
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class AnalysisStartRead(BaseModel):
    run: AnalysisRunSummary
    job_id: str


class ArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    media_id: str
    artifact_type: str
    content_type: str
    width: int
    height: int
    sha256: str


class PartDetectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    media_id: str
    model_version_id: str
    class_name: str
    confidence: float
    mask_area: int
    bbox_json: list[int]


class DamageDetectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    media_id: str
    model_version_id: str
    vehicle_part_detection_id: str | None
    class_name: str
    confidence: float
    severity: str
    coverage: float | None
    intersection_area: int
    region_count: int
    bbox_json: list[int]
    raw_output_json: dict[str, Any]


class FindingCorrectionCreate(BaseModel):
    action: Literal["ACCEPT", "REJECT", "CORRECT"]
    corrected_class: str | None = None
    corrected_part_detection_id: str | None = None
    corrected_severity: str | None = None
    notes: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def validate_corrected_values(self):
        corrected = self.corrected_class or self.corrected_part_detection_id or self.corrected_severity
        if self.action == "CORRECT" and not corrected:
            raise ValueError("A correction must change class, part, or severity")
        if self.action != "CORRECT" and corrected:
            raise ValueError("Corrected values are only valid for CORRECT actions")
        return self


class FindingCorrectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    analysis_run_id: str
    finding_type: str
    finding_id: str
    reviewer_id: str
    action: str
    corrected_class: str | None
    corrected_part_detection_id: str | None
    corrected_severity: str | None
    notes: str
    version: int
    created_at: datetime


class AnalysisResultRead(BaseModel):
    run: AnalysisRunSummary
    models: list[ModelVersionRead]
    artifacts: list[ArtifactRead]
    parts: list[PartDetectionRead]
    damages: list[DamageDetectionRead]
    corrections: list[FindingCorrectionRead]
    media: list[dict[str, Any]]
    taxonomy: dict[str, list[str]]
