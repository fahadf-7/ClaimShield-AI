# ClaimShield AI — Product Plan

## 1. Product Goal

Build a full-stack AI platform for vehicle inspection, accident-damage assessment, evidence verification, and fraud-risk analysis.

The product should be:

- Technically achievable using current pretrained models.
- Strong enough for a portfolio / FYP / startup prototype.
- Modular enough to evolve into a real B2B insurance SaaS product.
- Human-in-the-loop.
- Explainable.
- Designed for integration with existing insurer workflows.

The first version should **not** attempt to replace claims adjusters, surveyors, or insurance decision-makers.

---

# 2. Product Scope

## 2.1 In Scope

### Underwriting / Baseline Inspection

- Guided vehicle image capture.
- Required angle checklist.
- VIN capture.
- License plate capture.
- Vehicle identity validation.
- Vehicle-part segmentation.
- Existing damage detection.
- Baseline condition report.
- Historical vehicle inspection storage.

### Accident Claim Inspection

- Claim creation.
- Accident description.
- Image and video upload.
- Guided damage capture.
- Vehicle verification.
- Damage segmentation.
- Damage classification.
- Damage severity estimation.
- Damage-to-part mapping.
- Policy baseline comparison.
- Previous claim comparison.
- Duplicate / reused image detection.
- Metadata extraction.
- Manipulation detection.
- Evidence-risk scoring.
- Explainable findings.
- Surveyor review.
- AI-generated claim / inspection summary.

### Dashboard

- Claims list.
- Evidence-risk filters.
- Claim detail page.
- Vehicle history.
- Annotated images.
- Before / after comparisons.
- Damage tables.
- Forensic findings.
- AI summary.
- Reviewer decision.

---

## 2.2 Out of Scope for Initial Versions

Do not attempt these during the first product phases:

- Fully automated claim rejection.
- Fully automated fraud accusation.
- Exact repair-cost prediction.
- Exact payout calculation.
- Reliable estimation of damage age from a single photograph.
- Full accident reconstruction.
- Advanced 3D crash reconstruction.
- Large cross-insurer fraud networks.
- Real-time national insurance database integration.
- Automated structural / mechanical damage diagnosis from exterior photos.
- Training every CV model from scratch.

These may become future research or enterprise features.

---

# 3. Core Product Architecture

The platform should use a modular monolith initially.

```text
Frontend
    |
    v
FastAPI Backend
    |
    +-- Auth / User Management
    +-- Claims Module
    +-- Vehicle Module
    +-- Inspection Module
    +-- AI Orchestration Module
    +-- Risk Engine
    +-- Reporting Module
    |
    +-- Background Job Queue
            |
            +-- Vehicle / Part Model
            +-- Damage Model
            +-- Retrieval Pipeline
            +-- Forensics Pipeline
            +-- OCR
            +-- LLM Analysis

Data Layer
    |
    +-- PostgreSQL
    +-- pgvector
    +-- Object Storage
    +-- Redis
```

Do not split the system into microservices until scale requires it.

---

# 4. Recommended Technology Stack

## 4.1 Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- React Query / TanStack Query

Use for:

- Claims dashboard.
- Vehicle history.
- Inspection review.
- Annotated image viewer.
- Evidence-risk reports.
- Admin tools.

---

## 4.2 Claimant Capture Interface

Start with:

- Mobile-first Next.js PWA.

Later move to:

- React Native if required.

Main capture capabilities:

- Camera-first image capture.
- Guided angle sequence.
- Image quality validation.
- VIN image.
- License plate image.
- Damage close-ups.
- Optional walk-around video.

---

## 4.3 Backend

Use:

- FastAPI
- Python 3.11+
- SQLAlchemy
- Alembic
- Pydantic
- PostgreSQL

Reason:

The AI / CV stack is primarily Python-based, making FastAPI the simplest integration layer.

---

## 4.4 Database

Use:

### PostgreSQL

For:

- Users.
- Organizations.
- Vehicles.
- Policies.
- Claims.
- Inspections.
- Media.
- Damages.
- Risk signals.
- Review decisions.
- Reports.

### pgvector

For:

- Image embeddings.
- Historical visual search.

Avoid introducing a separate vector database initially unless scale requires it.

---

## 4.5 Object Storage

Use:

- Supabase Storage, S3, Cloudflare R2, or compatible object storage.

Store:

- Original images.
- Videos.
- Annotated images.
- Damage masks.
- Forensic heatmaps.
- Generated PDF / JSON reports.

---

## 4.6 Async Processing

Use:

- Celery + Redis

or:

- RQ + Redis

for the first version.

Tasks:

- Image inference.
- Video analysis.
- Embedding generation.
- Duplicate search.
- Forensic analysis.
- Report generation.

---

# 5. Computer Vision Architecture

The system should separate:

1. Vehicle parts.
2. Damage.

Do not use combinations such as:

- damaged_front_bumper
- scratched_left_door
- dented_rear_bumper

Instead:

### Model A — Vehicle Part Segmentation

Classes may include:

- Front bumper.
- Rear bumper.
- Hood.
- Trunk.
- Front-left door.
- Front-right door.
- Rear-left door.
- Rear-right door.
- Left fender.
- Right fender.
- Windshield.
- Rear windshield.
- Headlights.
- Taillights.
- Mirrors.
- Wheels.
- Roof.

### Model B — Damage Segmentation

Classes:

- Dent.
- Scratch.
- Crack.
- Broken.
- Glass shatter.
- Lamp broken.
- Paint chip.
- Missing part.
- Corrosion.

Then compute:

```text
Damage Mask ∩ Vehicle Part Mask
```

to determine:

```text
Front Left Door
    -> Dent
    -> Scratch
```

---

# 6. Recommended Models

## 6.1 Primary Damage / Part Model

Start with:

- YOLO11-seg or YOLO26-seg.

Recommended size:

- medium model for development.
- small model for lower-cost deployment.
- larger model only for benchmarking.

Recommended image size:

- 1024x1024 or higher where practical.

Reason:

Vehicle scratches and dents may become too small if images are aggressively resized.

---

## 6.2 Alternative Benchmark

Compare against one of:

- Mask R-CNN.
- Cascade Mask R-CNN.
- Mask2Former.

Use Detectron2 or MMDetection.

Do not build multiple production models initially. Use them only for evaluation.

---

## 6.3 SAM 2

Use SAM 2 for:

- Annotation assistance.
- Polygon refinement.
- Video object / damage tracking.
- Mask correction.

Do not use SAM 2 as the main damage classifier.

---

# 7. Dataset Strategy

## 7.1 Vehicle Damage

Start with:

### CarDD

Useful for:

- Dent.
- Scratch.
- Crack.
- Glass shatter.
- Lamp broken.
- Tire flat.

### Humans in the Loop — Car Parts and Damages

Useful because it contains both:

- Parts.
- Damage polygons.

### VehiDE

Use as an additional benchmark / training source after verifying quality and licensing.

---

## 7.2 Vehicle Parts

Use:

- Carparts-Seg.
- Humans in the Loop parts dataset.
- DSMLR Car Parts dataset.

---

## 7.3 Media Forensics

Use for research / benchmarking:

- CASIA.
- NIST / OpenMFC.
- CocoGlide.
- GenImage.

Most are generic image-forensics datasets, so they should not be the final domain-specific training source.

---

## 7.4 Custom ClaimShield Dataset

Create your own vehicle-specific dataset.

Generate or manually collect:

- Original vehicle photos.
- Edited damage.
- Added dents.
- Added scratches.
- Removed damage.
- Copy-move damage.
- Replaced license plates.
- AI-inpainted damage.
- Background replacement.
- Cropped images.
- Recompressed images.
- Screenshot images.
- Social-media-compressed images.

Labels:

```text
image_id
vehicle_id
is_manipulated
manipulation_type
manipulation_mask
damage_type
vehicle_part
source_image_id
```

This can become the product's proprietary training asset.

---

# 8. Damage Severity

Do not predict exact repair prices initially.

Use three severity classes:

- Minor.
- Moderate.
- Severe.

Inputs:

- Damage class.
- Vehicle part.
- Percentage of affected surface.
- Number of damage regions.
- Damage confidence.
- Safety criticality.

Example:

```text
Damage:
Left headlamp cracked

Affected area:
12%

Part criticality:
High

Output:
SEVERE
```

---

# 9. Damage-to-Part Mapping

For every detected damage mask:

1. Compute intersection with all part masks.
2. Assign the damage to the highest-overlap part.
3. Calculate:

```text
Damage Coverage =
Intersection(DamageMask, PartMask) / PartMask Area
```

Example:

```text
Front-left door:
Dent coverage = 14.8%
Scratch coverage = 3.1%
```

Store all results in the database.

---

# 10. Policy-Inception vs Claim-Time Comparison

This should become one of the strongest product features.

## Workflow

```text
Policy Inspection
        |
        v
Baseline Vehicle Condition
        |
        v
Stored Images + Damage Masks
        |
        |
Claim Inspection
        |
        v
Current Images + Damage Masks
        |
        v
Image / Part Alignment
        |
        v
Damage Comparison
```

Output each damage as:

- Pre-existing.
- New.
- Changed.
- Unknown.

---

## 10.1 Alignment Approach

Start with:

- Viewpoint matching.
- DINOv2 image embeddings.
- Local feature matching.
- Homography / geometric alignment where possible.
- Part-mask comparison.

Do not attempt pixel-perfect full-car registration for every angle initially.

Compare matching vehicle parts where confidence is sufficient.

---

# 11. Duplicate / Recycled Image Detection

Use a three-stage system.

## Stage 1 — Exact Duplicate

Use:

- SHA-256.

Detect exact files.

---

## Stage 2 — Near Duplicate

Use:

- pHash / dHash.

Detect:

- Resize.
- Compression.
- Minor color changes.

---

## Stage 3 — Semantic / Visual Match

Use:

- DINOv2 embeddings.
- pgvector nearest-neighbor search.

For every submitted image:

1. Generate embedding.
2. Search historical claim media.
3. Retrieve top-K similar images.
4. Apply threshold.

---

## Stage 4 — Geometric Verification

Use:

- LightGlue.

Confirm that candidate image pairs share enough local geometric features.

This reduces false positives.

---

# 12. Media Forensics

Do not depend on Error Level Analysis alone.

Build a multi-signal system.

## Signals

### Metadata

Extract:

- EXIF timestamp.
- Device make/model.
- GPS if present.
- Orientation.
- Dimensions.
- Software / editor metadata.
- Encoding information.

Flags:

- Capture time before reported accident.
- Unusual software signature.
- GPS conflict.
- Multiple incompatible devices across one inspection.

Missing metadata is not fraud.

---

## ELA

Use only as:

- Secondary visualization.
- Research signal.

Do not use it as proof of manipulation.

---

## Learned Manipulation Detector

Prototype with:

- TruFor or another image manipulation detection / localization model.

Important:

Check model licensing before commercial deployment.

For long-term product use, train or license a commercially suitable model.

---

## Generative Edit Detection

Train / test using:

- CocoGlide.
- Custom AI-inpainted vehicle damage.

Detect:

- AI-added dents.
- AI-added scratches.
- Removed damage.
- Generative fill.

---

## Provenance

Add:

- C2PA / Content Credentials verification where available.

Treat:

- valid provenance as positive evidence.
- missing provenance as neutral.

---

# 13. Vehicle Identity Verification

Capture:

- License plate.
- VIN.
- Vehicle overview.

## License Plate

Pipeline:

```text
Plate Detector
    ->
Crop
    ->
OCR
    ->
Normalize
    ->
Compare with policy
```

---

## VIN

Capture:

- Windshield VIN.
- Door-jamb VIN.

Use OCR to extract the 17-character VIN.

Validate:

- Length.
- Character rules.
- Policy match.

---

## Optional Visual Vehicle Classification

Later:

- Make.
- Model.
- Color.
- Body type.
- Approximate generation.

Use only as an additional consistency signal.

---

# 14. Guided Capture

This is a high-value product feature.

## Required Views

At policy inspection:

- Front.
- Front-left.
- Left side.
- Rear-left.
- Rear.
- Rear-right.
- Right side.
- Front-right.
- VIN.
- Odometer.
- Plate.

At claim time:

- Same overview angles.
- Multiple damage close-ups.
- Optional video.

---

## Capture Validation

Check:

- Blur.
- Brightness.
- Resolution.
- Vehicle visibility.
- Occlusion.
- Required angle.
- Correct object in frame.

Reject and retake low-quality images immediately.

---

# 15. Visual Liveness — Later Phase

For higher-risk claims, support guided video.

Prompt the user to perform randomly selected actions:

- Turn headlights on.
- Turn hazard lights on.
- Show front-left wheel.
- Walk clockwise.
- Open driver's door.

The system verifies the requested action.

Purpose:

- Reduce prerecorded video submission.
- Improve trust in remote inspections.

Do not place this in MVP.

---

# 16. Claim Narrative AI

The claimant provides a short accident description.

Example:

```text
"I was stopped and another car hit me from behind."
```

Use an LLM to convert it into structured JSON.

Example:

```json
{
  "collision_type": "rear_impact",
  "vehicle_state": "stationary",
  "expected_damage_regions": [
    "rear_bumper",
    "rear_left",
    "rear_right"
  ]
}
```

Do not ask the LLM to independently decide fraud.

---

# 17. Claim Consistency Engine

Compare:

- Claim description.
- Detected vehicle damage.
- Damage location.
- Baseline condition.
- Metadata.
- Historical image matches.

Example:

```text
Claim:
Rear collision

Detected:
No rear damage
Severe front-left damage

Consistency:
Low
```

Output an explainable signal.

---

# 18. Evidence Risk Engine

The first version should be rule-based and interpretable.

Possible inputs:

```text
duplicate_similarity
geometric_match_score
metadata_time_conflict
vehicle_identity_mismatch
prior_damage_overlap
manipulation_score
claim_consistency_score
capture_quality_score
```

Output:

```text
LOW
MEDIUM
HIGH
```

or:

```text
0-100 Evidence Risk Score
```

Do not call it:

- Fraud Probability.

until the system has been trained and calibrated on actual confirmed insurer outcomes.

---

## 18.1 Example Risk Logic

Example weights:

```text
Historical image match       25
Prior damage overlap         20
Vehicle identity mismatch    20
Manipulation indicators      15
Narrative inconsistency      10
Metadata anomaly             10
```

Weights should eventually be learned from insurer data.

---

# 19. AI Surveyor / Adjuster Assistant

Provide an LLM assistant that only reasons over structured claim data.

Example questions:

- Why was this claim flagged?
- Which damage appears pre-existing?
- Compare this claim with policy inception.
- Summarize all suspicious evidence.
- Generate surveyor notes.
- Show images matching previous claims.

The assistant should never invent evidence.

Use retrieval from:

- Claim data.
- Damage detections.
- Metadata.
- Historical matches.
- Reviewer notes.

---

# 20. Main Screens

## 20.1 Dashboard

Cards:

- Open claims.
- High-risk claims.
- Pending survey review.
- Claims completed.
- Average processing time.

Table:

```text
Claim ID
Vehicle
Customer
Date
Risk
Status
Reviewer
```

---

## 20.2 Claim Detail

Sections:

### Header

- Claim ID.
- Policy.
- Vehicle.
- Accident date.
- Status.
- Evidence risk.

### Evidence Risk Summary

Display:

- Main flags.
- Risk score.
- Recommendation.

### Damage Viewer

- Original image.
- Overlay masks.
- Toggle vehicle parts.
- Toggle damage.
- Confidence.

### Damage Table

```text
Part
Damage
Severity
Coverage
New / Previous
Confidence
```

### Historical Comparison

Side-by-side:

```text
Policy Inspection | Current Claim
```

### Duplicate Matches

Display:

- Submitted image.
- Historical match.
- Similarity.
- Claim ID.
- Date.

### Forensics

Display:

- Metadata.
- Manipulation score.
- Heatmap.
- ELA.
- Provenance.

### Claim Story

Show:

- User description.
- Structured extraction.
- Consistency score.

### Reviewer Action

- Approve evidence.
- Request more photos.
- Refer for physical inspection.
- Refer for investigation.
- Mark AI finding incorrect.

---

## 20.3 Vehicle History

Timeline:

```text
Policy Inspection
    ↓
Claim 1
    ↓
Renewal
    ↓
Claim 2
```

For each event:

- Images.
- Detected damage.
- Reviewer decision.

---

## 20.4 Capture Flow

Steps:

1. Introduction.
2. Camera permissions.
3. Vehicle front.
4. Front-left.
5. Left.
6. Rear-left.
7. Rear.
8. Rear-right.
9. Right.
10. Front-right.
11. VIN.
12. Plate.
13. Damage close-ups.
14. Review.
15. Submit.

---

# 21. Data Model

Core tables:

## users

```text
id
name
email
role
organization_id
```

## organizations

```text
id
name
type
```

Types:

- insurer
- surveyor_company
- fleet
- leasing_company

## vehicles

```text
id
registration_number
vin
make
model
year
color
```

## policies

```text
id
vehicle_id
policy_number
start_date
end_date
status
```

## claims

```text
id
policy_id
incident_date
incident_location
description
status
risk_score
risk_level
```

## inspections

```text
id
vehicle_id
claim_id
type
created_at
status
```

Types:

- policy_inception
- renewal
- claim
- post_repair

## media

```text
id
inspection_id
object_url
media_type
viewpoint
sha256
phash
embedding
metadata_json
```

## vehicle_parts

```text
id
media_id
part_type
confidence
mask_path
```

## damages

```text
id
media_id
vehicle_part_id
damage_type
severity
confidence
coverage
mask_path
```

## forensic_signals

```text
id
media_id
signal_type
score
details_json
```

## historical_matches

```text
id
source_media_id
matched_media_id
embedding_similarity
geometric_score
```

## risk_signals

```text
id
claim_id
signal_type
value
weight
explanation
```

## reviews

```text
id
claim_id
reviewer_id
decision
notes
created_at
```

---

# 22. API Structure

Example endpoints:

```text
POST   /auth/login

POST   /vehicles
GET    /vehicles/{id}
GET    /vehicles/{id}/history

POST   /policies
GET    /policies/{id}

POST   /claims
GET    /claims
GET    /claims/{id}

POST   /inspections
GET    /inspections/{id}

POST   /media/upload
GET    /media/{id}

POST   /claims/{id}/analyze
GET    /claims/{id}/analysis

GET    /claims/{id}/risk
GET    /claims/{id}/matches
GET    /claims/{id}/forensics

POST   /claims/{id}/review
POST   /claims/{id}/request-more-evidence

POST   /assistant/query
```

---

# 23. Background AI Workflow

After inspection submission:

```text
Upload Complete
      |
      v
Validate Media
      |
      +--> Hash
      +--> Metadata
      +--> Embedding
      |
      v
Vehicle / Part Segmentation
      |
      v
Damage Segmentation
      |
      v
Damage-Part Mapping
      |
      +--> Severity
      +--> Historical Baseline Compare
      +--> Duplicate Search
      +--> Forensic Analysis
      |
      v
Claim Narrative Parsing
      |
      v
Consistency Analysis
      |
      v
Evidence Risk Engine
      |
      v
AI Summary
      |
      v
Reviewer Dashboard
```

---

# 24. MLOps

Use:

- MLflow.
- DVC.
- Docker.
- GitHub Actions.
- Model versioning.
- Dataset versioning.

Track:

```text
model_version
dataset_version
training_date
metrics
thresholds
deployment_status
```

Do not introduce Kubernetes initially.

Deploy using:

- Docker Compose.
- GPU VM.
- Render / Railway / AWS / GCP / Azure depending budget.

Kubernetes can come later.

---

# 25. Evaluation

## 25.1 Damage Detection

Measure:

- mAP@50.
- mAP@50:95.
- Per-class AP.

---

## 25.2 Damage Segmentation

Measure:

- Mask mAP.
- IoU.
- Dice.

---

## 25.3 Part Segmentation

Measure:

- mIoU.
- Per-class IoU.

---

## 25.4 Duplicate Search

Measure:

- Precision@K.
- Recall@K.
- ROC-AUC.
- False-positive rate.

Test against:

- Resize.
- Crop.
- JPEG compression.
- Brightness changes.
- Screenshots.
- Partial edits.

---

## 25.5 Manipulation Detection

Measure:

- Image-level ROC-AUC.
- Pixel-level F1.
- IoU.
- False-positive rate.

---

## 25.6 Severity

Measure:

- Macro F1.
- Weighted F1.
- Confusion matrix.
- Quadratic weighted kappa.

---

# 26. Robustness Testing

Test with:

- Night photos.
- Bright sunlight.
- Rain.
- Dirty cars.
- Black cars.
- White cars.
- Metallic paint.
- Reflections.
- Motion blur.
- Low-end phone cameras.
- Compression.
- Screenshots.
- WhatsApp-quality media.
- Extreme close-ups.
- Tiny scratches.
- Different viewpoints.
- Partially visible vehicles.
- Aftermarket body parts.

---

# 27. Human-in-the-Loop Design

Every AI result should have:

- Confidence.
- Evidence.
- Reviewer correction.

Surveyors should be able to:

- Correct damage class.
- Change severity.
- Mark damage as pre-existing / new.
- Reject duplicate match.
- Reject forensic flag.
- Add notes.

Store corrections for future retraining.

This creates an active learning loop.

---

# 28. Product Phases

# Phase 0 — Foundation

## Goal

Create product skeleton and dataset pipeline.

## Features

- Project structure.
- Database.
- Auth.
- Organization.
- Vehicle CRUD.
- Policy CRUD.
- Claim CRUD.
- Media upload.
- Background jobs.
- Object storage.

## Output

A working claims web app without AI.

---

# Phase 1 — Damage Intelligence MVP

## Goal

Build the core CV product.

## Features

- Vehicle image upload.
- Part segmentation.
- Damage segmentation.
- Damage classification.
- Damage-to-part mapping.
- Severity classification.
- Annotated image generation.
- Claim damage viewer.

## AI

- YOLO11/YOLO26 segmentation.
- SAM 2 for annotation assistance.

## Output

The system can inspect a car and generate a structured damage report.

---

# Phase 2 — Policy Baseline & Historical Comparison

## Goal

Detect pre-existing damage.

## Features

- Policy-inception inspection.
- Vehicle inspection history.
- Viewpoint classification.
- Baseline images.
- Current vs baseline comparison.
- Part-level damage comparison.
- Classification:

```text
PRE_EXISTING
NEW
CHANGED
UNKNOWN
```

## Output

The system can determine whether visible damage was already present in previous inspections.

---

# Phase 3 — Recycled Image Intelligence

## Goal

Detect reused claim media.

## Features

- SHA-256.
- pHash.
- DINOv2 embeddings.
- pgvector search.
- Top-K historical matches.
- LightGlue verification.
- Similarity viewer.

## Output

The system can identify exact and near-duplicate claim images.

---

# Phase 4 — Media Forensics

## Goal

Detect suspicious digital evidence.

## Features

- EXIF extraction.
- Capture-time checks.
- Device checks.
- GPS checks.
- Editing-software signals.
- ELA visualization.
- Learned manipulation model.
- Forgery heatmap.
- C2PA verification.
- Vehicle-specific synthetic forgery dataset.

## Output

The system provides manipulation indicators and forensic evidence.

---

# Phase 5 — Verified Guided Capture

## Goal

Increase trust before images enter the system.

## Features

- Mobile-first capture.
- Required vehicle angles.
- Blur check.
- Brightness check.
- Viewpoint validation.
- Camera-only mode.
- VIN capture.
- Plate capture.
- Session timestamps.
- Media hashing.
- Optional location.

## Output

Insurers can remotely collect standardized inspection evidence.

---

# Phase 6 — Multimodal Claim Intelligence

## Goal

Integrate Generative AI meaningfully.

## Features

- Claim narrative parsing.
- Structured incident extraction.
- Expected damage-region prediction.
- CV vs narrative consistency.
- AI evidence explanation.
- Surveyor assistant.
- Auto-generated claim report.

## Output

A complete CV + AI claims analysis system.

---

# Phase 7 — Fraud Intelligence & Enterprise Layer

## Goal

Move beyond individual claims.

## Features

- Cross-claim vehicle matching.
- Image reuse networks.
- Device reuse.
- Repair-shop relationships.
- Claim graph.
- Risk-pattern rules.
- Graph anomaly detection.
- SIU dashboard.
- Enterprise APIs.

## Output

A B2B fraud-intelligence platform.

---

# 29. Recommended Initial Build Boundary

If this project must remain achievable, fully complete:

### Required

- Phase 0.
- Phase 1.
- Phase 2.
- Phase 3.
- Basic Phase 4.
- Basic Phase 6.

### Optional / Stretch

- Full forensic localization.
- Guided video.
- Liveness.
- Graph fraud.
- 3D damage estimation.
- Exact repair estimation.

This still produces a substantial product.

---

# 30. Best Final Demo Story

The strongest demo should show one vehicle across time.

## Policy Inception

Upload clean vehicle inspection.

System detects:

```text
Rear-right door:
Small pre-existing dent
```

---

## Claim

User reports:

```text
"Vehicle was hit from the front."
```

Uploads images.

System detects:

```text
Front bumper:
Moderate dent — NEW

Left headlamp:
Crack — NEW

Rear-right door:
Dent — PRE-EXISTING
```

---

## Fraud Signal

One uploaded close-up produces:

```text
94% historical image similarity
Matched Claim:
CLM-1032
```

---

## Forensics

System finds:

```text
Capture time conflict
Possible edited region
```

---

## AI Summary

```text
Evidence Risk: HIGH

Reasons:
- One submitted image closely matches a historical claim image.
- Rear-right door damage existed before the current incident.
- Current front damage is consistent with the reported collision.
- Metadata inconsistency detected in one image.

Recommendation:
Manual surveyor review.
```

This tells a complete product story:

**Inspection → Damage → History → Fraud Signals → AI Explanation → Human Decision**

---

# 31. Future Extensions

Possible later features:

- Repair-cost estimation using insurer / workshop data.
- Parts catalog integration.
- Workshop estimate validation.
- OCR of repair invoices.
- Total-loss support.
- Damage progression tracking.
- 3D dent measurement.
- Video-based damage reconstruction.
- Fleet inspection.
- Rental-car damage workflows.
- Leasing-return inspections.
- Used-car condition reports.
- Cross-insurer fraud federation.
- Insurance repository integration.
- Repair-shop fraud analytics.

---

# 32. Product Success Metrics

Track both ML and business metrics.

## AI Metrics

- Damage detection recall.
- Segmentation IoU.
- Duplicate-detection precision.
- Forensic false-positive rate.
- Prior-damage detection accuracy.

## Product Metrics

- Average inspection time.
- Claims automatically triaged.
- Manual survey time saved.
- Number of suspicious claims surfaced.
- Reviewer disagreement rate.
- Average time to claim assessment.
- Percentage of retakes due to poor evidence.
- Percentage of AI findings corrected by surveyors.

---

# 33. Final Recommended Product Positioning

Do not describe ClaimShield as:

> Car Damage Detection using YOLO.

Describe it as:

> **ClaimShield AI is an AI-powered motor inspection and claim evidence verification platform that combines computer vision, historical vehicle-condition comparison, image forensics, visual retrieval, and generative AI to help insurers determine what damage exists, what is new, whether submitted evidence can be trusted, and which claims require manual investigation.**

Core product message:

> **Verify first. Estimate second.**
