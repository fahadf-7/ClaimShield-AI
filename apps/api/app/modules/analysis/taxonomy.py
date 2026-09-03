from typing import Final

PART_TAXONOMY: Final[tuple[str, ...]] = (
    "FRONT_BUMPER",
    "REAR_BUMPER",
    "HOOD",
    "TRUNK",
    "FRONT_DOOR",
    "REAR_DOOR",
    "FENDER",
    "WINDSHIELD",
    "HEADLIGHT",
    "TAILLIGHT",
    "MIRROR",
    "WHEEL",
    "ROOF",
    "OTHER",
    "UNKNOWN",
)

DAMAGE_TAXONOMY: Final[tuple[str, ...]] = (
    "DENT",
    "SCRATCH",
    "CRACK",
    "BROKEN",
    "PAINT_CHIP",
    "MISSING_PART",
    "OTHER",
    "UNKNOWN",
)

PART_PROMPTS: Final[dict[str, str]] = {
    "FRONT_BUMPER": "the front bumper of the car",
    "REAR_BUMPER": "the rear bumper of the car",
    "HOOD": "the hood or bonnet of the car",
    "TRUNK": "the trunk or boot lid of the car",
    "FRONT_DOOR": "a front door of the car",
    "REAR_DOOR": "a rear door of the car",
    "FENDER": "a fender or quarter panel of the car",
    "WINDSHIELD": "the windshield of the car",
    "HEADLIGHT": "a headlight of the car",
    "TAILLIGHT": "a tail light of the car",
    "MIRROR": "a side mirror of the car",
    "WHEEL": "a wheel of the car",
    "ROOF": "the roof of the car",
}

DAMAGE_PROMPTS: Final[dict[str, str]] = {
    "DENT": "a visible dent on the vehicle body",
    "SCRATCH": "a visible scratch on the vehicle paint",
    "CRACK": "a visible crack on a vehicle component",
    "BROKEN": "a visibly broken vehicle component",
    "PAINT_CHIP": "chipped or flaking vehicle paint",
    "MISSING_PART": "a missing exterior vehicle part",
}

SAFETY_CRITICAL_PARTS: Final[frozenset[str]] = frozenset({"WINDSHIELD", "HEADLIGHT", "TAILLIGHT", "WHEEL"})

FIXTURE_PART_COLORS: Final[dict[str, tuple[int, int, int]]] = {
    "FRONT_BUMPER": (25, 95, 210),
    "REAR_BUMPER": (30, 140, 225),
    "HOOD": (20, 155, 105),
    "FRONT_DOOR": (15, 115, 90),
    "REAR_DOOR": (55, 165, 115),
    "FENDER": (30, 175, 185),
    "HEADLIGHT": (225, 205, 45),
}

FIXTURE_DAMAGE_COLORS: Final[dict[str, tuple[int, int, int]]] = {
    "DENT": (220, 35, 55),
    "SCRATCH": (245, 125, 25),
    "CRACK": (125, 45, 185),
    "BROKEN": (245, 195, 25),
}
