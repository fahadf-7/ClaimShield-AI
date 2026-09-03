from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from app.config import settings
from app.enums import ModelTask
from app.modules.analysis.taxonomy import (
    DAMAGE_PROMPTS,
    FIXTURE_DAMAGE_COLORS,
    FIXTURE_PART_COLORS,
    PART_PROMPTS,
)


@dataclass(frozen=True)
class SegmentationDetection:
    class_name: str
    confidence: float
    mask: np.ndarray
    raw_output: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AdapterMetadata:
    task: str
    name: str
    version: str
    adapter: str
    weights_checksum: str
    source: str
    license: str
    preprocessing: dict[str, Any]
    thresholds: dict[str, Any]
    class_mapping: dict[str, str]
    is_experimental: bool = True


class SegmentationAdapter(ABC):
    task: str
    device: str

    @property
    @abstractmethod
    def metadata(self) -> AdapterMetadata: ...

    @abstractmethod
    def predict(self, image: Image.Image) -> list[SegmentationDetection]: ...


class FixtureSegmentationAdapter(SegmentationAdapter):
    """Deterministic adapter for synthetic evaluation images, never real evidence."""

    def __init__(self, task: str) -> None:
        self.task = task
        self.device = "cpu"
        self._colors = FIXTURE_PART_COLORS if task == ModelTask.PART_SEGMENTATION.value else FIXTURE_DAMAGE_COLORS
        version_material = f"fixture-segmentation-v1:{task}:{sorted(self._colors.items())}"
        self._checksum = hashlib.sha256(version_material.encode()).hexdigest()

    @property
    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            task=self.task,
            name="claimshield-synthetic-fixture",
            version="1.0.0",
            adapter="fixture",
            weights_checksum=self._checksum,
            source="ClaimShield AI generated evaluation fixtures",
            license="CC0-1.0 synthetic fixtures",
            preprocessing={"color_space": "RGB", "color_tolerance": 10},
            thresholds={"minimum_pixels": 16},
            class_mapping={name: name for name in self._colors},
            is_experimental=True,
        )

    def predict(self, image: Image.Image) -> list[SegmentationDetection]:
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)
        detections: list[SegmentationDetection] = []
        for class_name, color in self._colors.items():
            distance = np.max(np.abs(pixels - np.asarray(color, dtype=np.int16)), axis=2)
            exact_mask = distance <= 10
            if int(exact_mask.sum()) < 16:
                continue
            mask = exact_mask
            if self.task == ModelTask.PART_SEGMENTATION.value:
                ys, xs = np.where(exact_mask)
                mask = np.zeros(exact_mask.shape, dtype=bool)
                mask[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1] = True
            detections.append(
                SegmentationDetection(
                    class_name=class_name,
                    confidence=0.99,
                    mask=mask,
                    raw_output={"adapter": "fixture", "evaluation_only": True},
                )
            )
        return detections


class ClipSegAdapter(SegmentationAdapter):
    """Zero-shot baseline; useful for experiments, not calibrated insurance evidence."""

    _runtime_cache: dict[tuple[str, str, str], tuple[Any, Any, Any]] = {}

    def __init__(self, task: str) -> None:
        self.task = task
        self._prompts = PART_PROMPTS if task == ModelTask.PART_SEGMENTATION.value else DAMAGE_PROMPTS
        self.device = self._detect_device()
        self._processor, self._model, weights_path = self._load_runtime()
        self._checksum = self._sha256_file(weights_path)

    @staticmethod
    def _detect_device() -> str:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def _load_runtime(self) -> tuple[Any, Any, Path]:
        import torch
        from transformers import CLIPSegForImageSegmentation, CLIPSegProcessor
        from transformers.utils.hub import cached_file

        cache_key = (settings.clipseg_model_id, settings.clipseg_revision, self.device)
        if cache_key not in self._runtime_cache:
            processor = CLIPSegProcessor.from_pretrained(
                settings.clipseg_model_id,
                revision=settings.clipseg_revision,
                cache_dir=settings.model_cache_directory,
                local_files_only=settings.ml_local_files_only,
                use_fast=False,
            )
            model = CLIPSegForImageSegmentation.from_pretrained(
                settings.clipseg_model_id,
                revision=settings.clipseg_revision,
                cache_dir=settings.model_cache_directory,
                local_files_only=settings.ml_local_files_only,
            ).to(self.device)
            model.eval()
            weights_file = cached_file(
                settings.clipseg_model_id,
                "model.safetensors",
                revision=settings.clipseg_revision,
                cache_dir=settings.model_cache_directory,
                local_files_only=settings.ml_local_files_only,
            )
            if weights_file is None:
                raise RuntimeError("CLIPSeg weights are unavailable")
            self._runtime_cache[cache_key] = (processor, model, Path(weights_file))
            if self.device == "cuda":
                torch.cuda.empty_cache()
        return self._runtime_cache[cache_key]

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @property
    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            task=self.task,
            name=settings.clipseg_model_id,
            version=settings.clipseg_revision,
            adapter="clipseg",
            weights_checksum=self._checksum,
            source=f"https://huggingface.co/{settings.clipseg_model_id}",
            license="Apache-2.0 model-card metadata; verify before commercial use",
            preprocessing={"processor": "CLIPSegProcessor", "input_size": 352, "color_space": "RGB"},
            thresholds={
                "mask_probability": settings.analysis_mask_threshold,
                "minimum_mask_ratio": settings.analysis_min_mask_ratio,
            },
            class_mapping=dict(self._prompts),
            is_experimental=True,
        )

    def predict(self, image: Image.Image) -> list[SegmentationDetection]:
        import torch
        import torch.nn.functional as functional

        prompts = list(self._prompts.values())
        classes = list(self._prompts.keys())
        inputs = self._processor(text=prompts, padding=True, return_tensors="pt")
        image_inputs = self._processor(images=[image] * len(prompts), return_tensors="pt")
        inputs["pixel_values"] = image_inputs["pixel_values"]
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        with torch.inference_mode():
            logits = self._model(**inputs).logits.unsqueeze(1)
            resized = functional.interpolate(
                logits,
                size=(image.height, image.width),
                mode="bilinear",
                align_corners=False,
            ).squeeze(1)
            probabilities = resized.sigmoid().cpu().numpy()
        detections: list[SegmentationDetection] = []
        total_pixels = image.width * image.height
        for class_name, probability in zip(classes, probabilities, strict=True):
            mask = probability >= settings.analysis_mask_threshold
            area = int(mask.sum())
            if area / total_pixels < settings.analysis_min_mask_ratio:
                continue
            confidence = float(probability[mask].mean())
            detections.append(
                SegmentationDetection(
                    class_name=class_name,
                    confidence=confidence,
                    mask=mask,
                    raw_output={
                        "prompt": self._prompts[class_name],
                        "threshold": settings.analysis_mask_threshold,
                        "calibrated": False,
                    },
                )
            )
        return detections


def create_analysis_adapters() -> tuple[SegmentationAdapter, SegmentationAdapter]:
    adapter = settings.analysis_adapter.strip().lower()
    if adapter == "fixture":
        return (
            FixtureSegmentationAdapter(ModelTask.PART_SEGMENTATION.value),
            FixtureSegmentationAdapter(ModelTask.DAMAGE_SEGMENTATION.value),
        )
    if adapter == "clipseg":
        return (
            ClipSegAdapter(ModelTask.PART_SEGMENTATION.value),
            ClipSegAdapter(ModelTask.DAMAGE_SEGMENTATION.value),
        )
    raise ValueError(f"Unsupported analysis adapter: {settings.analysis_adapter}")
