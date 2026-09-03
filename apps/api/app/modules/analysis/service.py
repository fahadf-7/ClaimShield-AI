from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from io import BytesIO
from uuid import uuid4

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common import new_id, utcnow
from app.config import settings
from app.enums import AnalysisState
from app.modules.analysis.adapters import AdapterMetadata, SegmentationAdapter, create_analysis_adapters
from app.modules.analysis.geometry import (
    assign_damage_to_part,
    calculate_severity,
    count_regions,
    mask_bbox,
)
from app.modules.analysis.models import (
    AnalysisRun,
    DamageDetection,
    DerivedArtifact,
    ModelVersion,
    VehiclePartDetection,
)
from app.modules.media.models import Media
from app.storage import ObjectStorage, get_storage

AdapterFactory = Callable[[], tuple[SegmentationAdapter, SegmentationAdapter]]

PART_OVERLAY_COLOR = (3, 105, 161, 72)
DAMAGE_OVERLAY_COLORS = {
    "DENT": (220, 38, 38, 150),
    "SCRATCH": (234, 88, 12, 165),
    "CRACK": (126, 34, 206, 165),
    "BROKEN": (185, 28, 28, 180),
    "PAINT_CHIP": (180, 83, 9, 160),
    "MISSING_PART": (153, 27, 27, 180),
}


def _image_bytes(image: Image.Image, format_name: str) -> bytes:
    buffer = BytesIO()
    save_image = image.convert("RGB") if format_name == "JPEG" else image
    save_image.save(buffer, format=format_name, quality=88, optimize=True)
    return buffer.getvalue()


def _mask_bytes(mask: np.ndarray) -> bytes:
    image = Image.fromarray(np.where(mask, 255, 0).astype(np.uint8))
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def _store_artifact(
    db: Session,
    storage: ObjectStorage,
    run: AnalysisRun,
    media: Media,
    artifact_type: str,
    data: bytes,
    content_type: str,
    width: int,
    height: int,
    extension: str,
) -> DerivedArtifact:
    key = f"{run.organization_id}/derived/{run.id[:12]}/{uuid4()}.{extension}"
    storage.put(key, data, content_type)
    artifact = DerivedArtifact(
        id=new_id(),
        organization_id=run.organization_id,
        analysis_run_id=run.id,
        media_id=media.id,
        artifact_type=artifact_type,
        object_key=key,
        content_type=content_type,
        width=width,
        height=height,
        sha256=hashlib.sha256(data).hexdigest(),
    )
    db.add(artifact)
    return artifact


def _register_model(db: Session, metadata: AdapterMetadata) -> ModelVersion:
    model = db.scalar(
        select(ModelVersion).where(
            ModelVersion.task == metadata.task,
            ModelVersion.name == metadata.name,
            ModelVersion.version == metadata.version,
        )
    )
    if model is not None:
        if model.weights_checksum != metadata.weights_checksum:
            raise RuntimeError("Registered model checksum does not match loaded weights")
        return model
    model = ModelVersion(
        id=new_id(),
        task=metadata.task,
        name=metadata.name,
        version=metadata.version,
        adapter=metadata.adapter,
        weights_checksum=metadata.weights_checksum,
        source=metadata.source,
        license=metadata.license,
        preprocessing_json=metadata.preprocessing,
        thresholds_json=metadata.thresholds,
        class_mapping_json=metadata.class_mapping,
        is_experimental=metadata.is_experimental,
    )
    db.add(model)
    db.flush()
    return model


def _working_image(data: bytes) -> Image.Image:
    with Image.open(BytesIO(data)) as source:
        normalized = ImageOps.exif_transpose(source).convert("RGB")
    normalized.thumbnail(
        (settings.analysis_max_working_size, settings.analysis_max_working_size),
        Image.Resampling.LANCZOS,
    )
    return normalized


def _overlay(
    image: Image.Image,
    parts: list[tuple[VehiclePartDetection, np.ndarray]],
    damages: list[tuple[DamageDetection, np.ndarray]],
) -> Image.Image:
    composed = image.convert("RGBA")
    for finding, mask in parts:
        layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        layer.paste(PART_OVERLAY_COLOR, mask=Image.fromarray(np.where(mask, 255, 0).astype(np.uint8)))
        composed = Image.alpha_composite(composed, layer)
        if finding.bbox_json:
            draw = ImageDraw.Draw(composed)
            draw.rectangle(finding.bbox_json, outline=(3, 105, 161, 230), width=2)
            draw.text(
                (finding.bbox_json[0] + 4, finding.bbox_json[1] + 4),
                finding.class_name,
                fill=(255, 255, 255, 255),
                stroke_width=2,
                stroke_fill=(3, 70, 110, 255),
            )
    for finding, mask in damages:
        color = DAMAGE_OVERLAY_COLORS.get(finding.class_name, (185, 28, 28, 150))
        layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        layer.paste(color, mask=Image.fromarray(np.where(mask, 255, 0).astype(np.uint8)))
        composed = Image.alpha_composite(composed, layer)
        if finding.bbox_json:
            draw = ImageDraw.Draw(composed)
            label = f"{finding.class_name} · {finding.severity}"
            draw.rectangle(finding.bbox_json, outline=color[:3] + (255,), width=3)
            draw.text(
                (finding.bbox_json[0] + 4, finding.bbox_json[1] + 4),
                label,
                fill=(255, 255, 255, 255),
                stroke_width=2,
                stroke_fill=(95, 20, 20, 255),
            )
    return composed


def _transparent_overlay(
    image: Image.Image,
    findings: list[tuple[VehiclePartDetection | DamageDetection, np.ndarray]],
    damage: bool,
) -> Image.Image:
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    for finding, mask in findings:
        color = (
            DAMAGE_OVERLAY_COLORS.get(finding.class_name, (185, 28, 28, 150))
            if damage
            else PART_OVERLAY_COLOR
        )
        layer.paste(
            color,
            mask=Image.fromarray(np.where(mask, 255, 0).astype(np.uint8)),
        )
    return layer


def execute_analysis_run(
    db: Session,
    run_id: str,
    storage: ObjectStorage | None = None,
    adapter_factory: AdapterFactory = create_analysis_adapters,
) -> dict[str, object]:
    storage = storage or get_storage()
    run = db.get(AnalysisRun, run_id)
    if run is None:
        raise ValueError("Analysis run not found")
    if run.state in {AnalysisState.SUCCEEDED.value, AnalysisState.PARTIAL.value}:
        return {"analysis_run_id": run.id, "state": run.state}
    run.state = AnalysisState.RUNNING.value
    run.started_at = utcnow()
    db.commit()
    started = time.perf_counter()
    warnings: list[str] = []
    processed_media = 0
    failed_stages = 0
    total_stages = 0
    try:
        part_adapter, damage_adapter = adapter_factory()
        part_model = _register_model(db, part_adapter.metadata)
        damage_model = _register_model(db, damage_adapter.metadata)
        run.part_model_version_id = part_model.id
        run.damage_model_version_id = damage_model.id
        run.device = (
            part_adapter.device
            if part_adapter.device == damage_adapter.device
            else f"{part_adapter.device}/{damage_adapter.device}"
        )
        media_items = list(
            db.scalars(
                select(Media).where(
                    Media.inspection_id == run.inspection_id,
                    Media.organization_id == run.organization_id,
                )
            )
        )
        if not media_items:
            raise ValueError("Inspection has no media to analyze")
        for media in media_items:
            image = _working_image(storage.get(media.object_key))
            normalized_bytes = _image_bytes(image, "JPEG")
            _store_artifact(
                db, storage, run, media, "NORMALIZED", normalized_bytes, "image/jpeg", image.width, image.height, "jpg"
            )
            thumbnail = image.copy()
            thumbnail.thumbnail((480, 360), Image.Resampling.LANCZOS)
            _store_artifact(
                db,
                storage,
                run,
                media,
                "THUMBNAIL",
                _image_bytes(thumbnail, "JPEG"),
                "image/jpeg",
                thumbnail.width,
                thumbnail.height,
                "jpg",
            )

            part_outputs = []
            damage_outputs = []
            for stage_name, adapter in (("part", part_adapter), ("damage", damage_adapter)):
                total_stages += 1
                try:
                    output = adapter.predict(image)
                    if stage_name == "part":
                        part_outputs = output
                    else:
                        damage_outputs = output
                except Exception:
                    failed_stages += 1
                    warnings.append(f"{media.original_filename}: {stage_name} segmentation failed")

            persisted_parts: list[tuple[VehiclePartDetection, np.ndarray]] = []
            for output in part_outputs:
                mask = np.asarray(output.mask, dtype=bool)
                if not mask.any():
                    continue
                finding = VehiclePartDetection(
                    id=new_id(),
                    organization_id=run.organization_id,
                    analysis_run_id=run.id,
                    media_id=media.id,
                    model_version_id=part_model.id,
                    class_name=output.class_name,
                    confidence=output.confidence,
                    mask_key="pending",
                    mask_area=int(mask.sum()),
                    bbox_json=mask_bbox(mask),
                    raw_output_json=output.raw_output,
                )
                mask_data = _mask_bytes(mask)
                artifact = _store_artifact(
                    db,
                    storage,
                    run,
                    media,
                    f"PART_MASK_{finding.id}",
                    mask_data,
                    "image/png",
                    image.width,
                    image.height,
                    "png",
                )
                finding.mask_key = artifact.object_key
                db.add(finding)
                persisted_parts.append((finding, mask))

            persisted_damages: list[tuple[DamageDetection, np.ndarray]] = []
            part_candidates = [(finding.id, finding.class_name, mask) for finding, mask in persisted_parts]
            for output in damage_outputs:
                mask = np.asarray(output.mask, dtype=bool)
                if not mask.any():
                    continue
                assignment = assign_damage_to_part(mask, part_candidates)
                regions = count_regions(mask)
                severity = calculate_severity(
                    output.class_name, assignment.class_name, assignment.coverage, regions, output.confidence
                )
                raw = dict(output.raw_output)
                raw["part_assignment"] = {
                    "part_class": assignment.class_name,
                    "overlap_fraction": assignment.overlap_fraction,
                    "reason": assignment.reason,
                }
                finding = DamageDetection(
                    id=new_id(),
                    organization_id=run.organization_id,
                    analysis_run_id=run.id,
                    media_id=media.id,
                    model_version_id=damage_model.id,
                    vehicle_part_detection_id=assignment.detection_id,
                    class_name=output.class_name,
                    confidence=output.confidence,
                    severity=severity,
                    coverage=assignment.coverage,
                    intersection_area=assignment.intersection_area,
                    region_count=regions,
                    mask_key="pending",
                    bbox_json=mask_bbox(mask),
                    raw_output_json=raw,
                )
                artifact = _store_artifact(
                    db,
                    storage,
                    run,
                    media,
                    f"DAMAGE_MASK_{finding.id}",
                    _mask_bytes(mask),
                    "image/png",
                    image.width,
                    image.height,
                    "png",
                )
                finding.mask_key = artifact.object_key
                db.add(finding)
                persisted_damages.append((finding, mask))

            if not persisted_parts:
                warnings.append(f"{media.original_filename}: no supported part detected; part is UNKNOWN")
            if not persisted_damages:
                warnings.append(f"{media.original_filename}: no supported visible damage detected")
            part_layer = _transparent_overlay(image, persisted_parts, damage=False)
            _store_artifact(
                db,
                storage,
                run,
                media,
                "PARTS_OVERLAY",
                _image_bytes(part_layer, "PNG"),
                "image/png",
                image.width,
                image.height,
                "png",
            )
            damage_layer = _transparent_overlay(image, persisted_damages, damage=True)
            _store_artifact(
                db,
                storage,
                run,
                media,
                "DAMAGE_OVERLAY",
                _image_bytes(damage_layer, "PNG"),
                "image/png",
                image.width,
                image.height,
                "png",
            )
            overlay = _overlay(image, persisted_parts, persisted_damages)
            _store_artifact(
                db,
                storage,
                run,
                media,
                "COMBINED_OVERLAY",
                _image_bytes(overlay, "PNG"),
                "image/png",
                image.width,
                image.height,
                "png",
            )
            processed_media += 1
            db.flush()

        if total_stages and failed_stages == total_stages:
            raise RuntimeError("All segmentation stages failed")
        run.state = AnalysisState.PARTIAL.value if failed_stages else AnalysisState.SUCCEEDED.value
        run.warnings_json = warnings
        run.timings_json = {
            "total_seconds": round(time.perf_counter() - started, 4),
            "media_count": processed_media,
            "failed_stages": failed_stages,
            "total_stages": total_stages,
        }
        run.completed_at = utcnow()
        db.commit()
        return {
            "analysis_run_id": run.id,
            "state": run.state,
            "media_count": processed_media,
            "warnings": warnings,
        }
    except Exception:
        db.rollback()
        failed_run = db.get(AnalysisRun, run_id)
        if failed_run is not None:
            failed_run.state = AnalysisState.FAILED.value
            failed_run.error_category = "DAMAGE_ANALYSIS_ERROR"
            failed_run.error_message = "Damage analysis could not be completed."
            failed_run.completed_at = utcnow()
            failed_run.timings_json = {"total_seconds": round(time.perf_counter() - started, 4)}
            db.commit()
        raise
