# Phase 1 Canonical Taxonomy

Parts and damage remain separate labels. A finding may use `OTHER` when visible evidence is outside the supported taxonomy and `UNKNOWN` when the evidence or mapping is insufficient.

## Vehicle parts

`FRONT_BUMPER`, `REAR_BUMPER`, `HOOD`, `TRUNK`, `FRONT_DOOR`, `REAR_DOOR`, `FENDER`, `WINDSHIELD`, `HEADLIGHT`, `TAILLIGHT`, `MIRROR`, `WHEEL`, `ROOF`, `OTHER`, `UNKNOWN`

Left/right distinctions are deferred until representative data supports them consistently. The source image viewpoint remains available as context.

## Exterior damage

`DENT`, `SCRATCH`, `CRACK`, `BROKEN`, `PAINT_CHIP`, `MISSING_PART`, `OTHER`, `UNKNOWN`

Phase 1 does not infer damage age, repair price, structural condition, or claim validity.

## Initial external-label mapping

| External concept | ClaimShield label |
|---|---|
| Dent | `DENT` |
| Scratch | `SCRATCH` |
| Cracked | `CRACK` |
| Broken part, lamp broken, glass shatter | `BROKEN` |
| Flaking, paint chip | `PAINT_CHIP` |
| Missing part | `MISSING_PART` |
| Corrosion or unsupported visible damage | `OTHER` |
| Ambiguous, low-confidence, unmapped | `UNKNOWN` |

Severity is a transparent rule based on visible-part coverage, damage class, region count, confidence, and limited part criticality. It is not repair or structural severity.
