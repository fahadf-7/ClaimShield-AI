from dataclasses import dataclass

import numpy as np

from app.config import settings
from app.enums import DamageSeverity
from app.modules.analysis.taxonomy import SAFETY_CRITICAL_PARTS


@dataclass(frozen=True)
class PartAssignment:
    detection_id: str | None
    class_name: str
    intersection_area: int
    coverage: float | None
    overlap_fraction: float
    reason: str | None = None


def clip_mask(mask: np.ndarray) -> np.ndarray:
    if mask.ndim != 2:
        raise ValueError("Segmentation masks must be two-dimensional")
    return np.asarray(mask, dtype=bool)


def mask_bbox(mask: np.ndarray) -> list[int]:
    clipped = clip_mask(mask)
    ys, xs = np.where(clipped)
    if not len(xs):
        return []
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def mask_intersection(left: np.ndarray, right: np.ndarray) -> int:
    left_mask = clip_mask(left)
    right_mask = clip_mask(right)
    if left_mask.shape != right_mask.shape:
        raise ValueError("Masks must have the same dimensions")
    return int(np.logical_and(left_mask, right_mask).sum())


def count_regions(mask: np.ndarray) -> int:
    remaining = clip_mask(mask).copy()
    height, width = remaining.shape
    regions = 0
    for y in range(height):
        for x in range(width):
            if not remaining[y, x]:
                continue
            regions += 1
            stack = [(y, x)]
            remaining[y, x] = False
            while stack:
                current_y, current_x = stack.pop()
                for next_y, next_x in (
                    (current_y - 1, current_x),
                    (current_y + 1, current_x),
                    (current_y, current_x - 1),
                    (current_y, current_x + 1),
                ):
                    if 0 <= next_y < height and 0 <= next_x < width and remaining[next_y, next_x]:
                        remaining[next_y, next_x] = False
                        stack.append((next_y, next_x))
    return regions


def assign_damage_to_part(
    damage_mask: np.ndarray,
    parts: list[tuple[str, str, np.ndarray]],
) -> PartAssignment:
    damage = clip_mask(damage_mask)
    damage_area = int(damage.sum())
    if damage_area == 0 or not parts:
        return PartAssignment(None, "UNKNOWN", 0, None, 0.0, "No compatible visible part")
    candidates: list[tuple[float, int, int, str, str]] = []
    for detection_id, class_name, part_mask in parts:
        part = clip_mask(part_mask)
        intersection = mask_intersection(damage, part)
        part_area = int(part.sum())
        overlap = intersection / damage_area
        candidates.append((overlap, intersection, part_area, detection_id, class_name))
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    best = candidates[0]
    if best[0] < settings.analysis_min_part_overlap:
        return PartAssignment(None, "UNKNOWN", best[1], None, best[0], "Part overlap below threshold")
    if len(candidates) > 1 and best[0] - candidates[1][0] < settings.analysis_tie_margin:
        return PartAssignment(None, "UNKNOWN", best[1], None, best[0], "Multiple parts have similar overlap")
    coverage = best[1] / best[2] if best[2] else None
    return PartAssignment(best[3], best[4], best[1], coverage, best[0])


def calculate_severity(
    damage_class: str,
    part_class: str,
    coverage: float | None,
    region_count: int,
    confidence: float,
) -> str:
    if coverage is None or confidence < 0.60:
        return DamageSeverity.UNKNOWN.value
    if damage_class in {"BROKEN", "MISSING_PART"} and part_class in SAFETY_CRITICAL_PARTS:
        return DamageSeverity.SEVERE.value
    if damage_class == "CRACK" and part_class in SAFETY_CRITICAL_PARTS and coverage >= 0.02:
        return DamageSeverity.SEVERE.value
    level = 1 if coverage < 0.03 else 2 if coverage < 0.12 else 3
    if damage_class in {"BROKEN", "MISSING_PART"}:
        level = max(level, 2)
    if region_count >= 3:
        level = min(3, level + 1)
    return {
        1: DamageSeverity.MINOR.value,
        2: DamageSeverity.MODERATE.value,
        3: DamageSeverity.SEVERE.value,
    }[level]
