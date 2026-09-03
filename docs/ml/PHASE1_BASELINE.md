# Phase 1 Baseline and Limitations

## Reproducible application baseline

The default `fixture` adapter recognizes exact color-coded regions in generated synthetic images. Its purpose is to verify the analysis data path, artifact generation, mask geometry, severity rules, authorization, reviewer corrections, and UI behavior. It is not a vehicle-damage model and must never be used to interpret real claim evidence.

The fixed `phase1-fixtures-v1` manifest contains no customer media and defines expected part and damage regions. Exact fixture recognition is expected by construction; those results are not reported as real-world ML accuracy.

## Optional pretrained exploratory baseline

Set `ANALYSIS_ADAPTER=clipseg` to use the pretrained `CIDAS/clipseg-rd64-refined` zero-shot adapter. The worker downloads and checksums the configured revision, records CPU/GPU selection, and stores the prompts and thresholds with each model version. CLIPSeg was not trained or calibrated for motor-insurance damage, so its findings remain experimental and may be absent or incorrect.

The pinned revision was smoke-tested on CPU on 2026-09-03. Its `model.safetensors` SHA-256 is `d00ca85d6b859f9d07b7cfb8ef26fe9771cb275b34c9368f2ecf603139307f55`.

## Metrics status

Representative part mIoU/per-class IoU, damage mask mAP/IoU/Dice, and per-class precision/recall are **not yet established**. They require an approved, vehicle-grouped validation dataset. Phase 1 must remain `In review` until those metrics and failure examples are recorded.

## Known failure modes

- Tiny scratches, glare, reflections, dirt, shadows, and compression may be confused with damage.
- Extreme close-ups may not contain enough evidence to assign a vehicle part.
- Generic zero-shot prompts can produce overlapping or semantically weak masks.
- Coverage describes the visible part mask in one image, not the full physical part.
- `UNKNOWN` or no finding is the correct output when confidence or overlap is insufficient.
