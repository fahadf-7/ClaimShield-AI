import numpy as np

from app.modules.analysis.geometry import (
    assign_damage_to_part,
    calculate_severity,
    count_regions,
    mask_bbox,
    mask_intersection,
)


def test_mask_geometry_and_part_assignment():
    left = np.zeros((20, 20), dtype=bool)
    right = np.zeros((20, 20), dtype=bool)
    damage = np.zeros((20, 20), dtype=bool)
    left[2:18, 1:9] = True
    right[2:18, 11:19] = True
    damage[6:12, 3:8] = True

    assert mask_bbox(damage) == [3, 6, 8, 12]
    assert mask_intersection(left, damage) == 30
    assignment = assign_damage_to_part(
        damage,
        [("left-id", "FRONT_DOOR", left), ("right-id", "REAR_DOOR", right)],
    )
    assert assignment.detection_id == "left-id"
    assert assignment.class_name == "FRONT_DOOR"
    assert assignment.coverage == 30 / 128


def test_empty_and_tied_part_assignments_return_unknown():
    damage = np.zeros((10, 10), dtype=bool)
    damage[4:6, 4:6] = True
    assert assign_damage_to_part(damage, []).class_name == "UNKNOWN"

    first = np.zeros((10, 10), dtype=bool)
    second = np.zeros((10, 10), dtype=bool)
    first[:, :5] = True
    second[:, 5:] = True
    tied_damage = np.zeros((10, 10), dtype=bool)
    tied_damage[4:6, 4:6] = True
    tied = assign_damage_to_part(
        tied_damage,
        [("one", "HOOD", first), ("two", "FENDER", second)],
    )
    assert tied.class_name == "UNKNOWN"
    assert tied.reason == "Multiple parts have similar overlap"


def test_region_count_and_severity_boundaries():
    mask = np.zeros((12, 12), dtype=bool)
    mask[1:3, 1:3] = True
    mask[6:9, 7:10] = True
    assert count_regions(mask) == 2
    assert calculate_severity("DENT", "FRONT_DOOR", 0.01, 1, 0.90) == "MINOR"
    assert calculate_severity("DENT", "FRONT_DOOR", 0.07, 1, 0.90) == "MODERATE"
    assert calculate_severity("DENT", "FRONT_DOOR", 0.15, 1, 0.90) == "SEVERE"
    assert calculate_severity("CRACK", "HEADLIGHT", 0.02, 1, 0.90) == "SEVERE"
    assert calculate_severity("DENT", "FRONT_DOOR", 0.10, 1, 0.40) == "UNKNOWN"
