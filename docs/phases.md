# ClaimShield AI — Implementation Phases

## 1. How to use this document

This is the implementation source of truth for the personal-project version of ClaimShield AI. `docs/plan.md` remains the broader product and research reference.

Rules for using this roadmap:

1. Work on only one phase at a time.
2. Complete the phase in the order listed: data model, backend, jobs/AI, frontend, tests, documentation.
3. Do not mark a phase complete until every required exit check passes.
4. Record intentional deviations under the affected phase before implementing them.
5. Keep experimental capabilities clearly labelled and separated from trusted findings.
6. Prefer `UNKNOWN` or “insufficient evidence” over unsupported certainty.

Update the status table as work progresses:

| Phase | Name | Status | MVP requirement |
|---|---|---|---|
| 0 | Foundation | In review | Required |
| 1 | Damage Intelligence | In progress | Required |
| 2 | Policy Baseline Comparison | Not started | Required |
| 3 | Reused Image Intelligence | Not started | Required |
| 4 | Basic Media Forensics | Not started | Required, basic scope only |
| 5 | Guided Capture and Vehicle Identity | Not started | Required for complete product flow |
| 6 | Claim Intelligence, Risk, and Reporting | Not started | Required |
| 7 | Evaluation, Security, and Release | Not started | Required before final release/demo |
| 8 | Enterprise and Research Extensions | Deferred | Not part of personal-project MVP |

Allowed status values are `Not started`, `In progress`, `Blocked`, `In review`, and `Complete`.

## 2. Delivery boundary

### 2.1 MVP outcome

The MVP must demonstrate one complete vehicle history:

```text
Policy inspection
→ trusted baseline condition
→ claim inspection
→ damage and part analysis
→ new/pre-existing comparison
→ reused-image and metadata checks
→ explainable evidence-risk report
→ human reviewer decision/correction
```

### 2.2 Included in the MVP

- Passenger vehicles and still images.
- One insurer organization, while keeping all data organization-scoped.
- Admin, reviewer/surveyor, and claimant access paths.
- Vehicle, policy, claim, inspection, media, and review workflows.
- Policy-inception, renewal, and claim inspections.
- Separate vehicle-part and damage segmentation.
- Damage-to-part mapping, coverage, confidence, and rule-based severity.
- Part/viewpoint-level comparison with `PRE_EXISTING`, `NEW`, `CHANGED`, or `UNKNOWN` output.
- Exact, near-duplicate, and semantic image retrieval.
- Metadata, provenance, and basic manipulation indicators.
- Guided mobile web capture, image-quality checks, VIN, and plate capture.
- Structured claim narrative extraction and consistency checks.
- Versioned, explainable evidence-risk rules.
- Human corrections, audit history, and JSON/PDF evidence reports.

### 2.3 Explicitly excluded from the MVP

- Automatic claim approval, rejection, pricing, payout, or fraud accusation.
- Exact repair-cost prediction.
- Reliable damage-age estimation from one photograph.
- Mechanical or structural diagnosis from exterior images.
- Native mobile applications.
- Guided video, visual liveness, and accident/3D reconstruction.
- Cross-insurer data sharing, national databases, and graph fraud networks.
- Claims that every digital manipulation or generative edit can be detected.
- Training every computer-vision model from scratch.

## 3. Architecture and technology baseline

### 3.1 Application stack

| Area | Required default | Notes |
|---|---|---|
| Web application | Next.js, TypeScript, Tailwind CSS, shadcn/ui | Mobile-first capture and desktop reviewer UI in one app |
| Server state | TanStack Query | Centralize query keys, loading, error, and invalidation behavior |
| Forms/contracts | Typed forms plus generated or shared API types | Validate on client and server; server remains authoritative |
| Backend | FastAPI, Python 3.11+, Pydantic, SQLAlchemy, Alembic | Organize by business module inside one deployable backend |
| Database | PostgreSQL | Source of truth for product and analysis metadata |
| Vector search | pgvector | Keep embeddings in PostgreSQL for the MVP |
| Object storage | Private S3-compatible storage | Use signed access; local compatible storage is acceptable in development |
| Background jobs | Celery with Redis | Run workers in containers for consistent local behavior |
| Computer vision | PyTorch-compatible segmentation pipeline | Start with a pretrained YOLO-seg baseline; benchmark before fine-tuning |
| Image retrieval | SHA-256, pHash, DINOv2, optional LightGlue | Use staged retrieval and verification |
| OCR | Benchmarked plate/VIN detector plus OCR engine | Allow manual correction; keep the provider replaceable |
| LLM | Provider adapter with structured JSON output | Narrative parsing and grounded summaries only |
| Testing | pytest, backend integration tests, frontend unit/component tests, Playwright | Add fixed ML evaluation sets alongside application tests |
| Delivery | Docker Compose and CI | No Kubernetes or microservices in the MVP |
| Experiment tracking | Lightweight version registry initially; MLflow/DVC when training begins | Always record model, dataset, threshold, and rule versions |

Pin working dependency versions in lockfiles. Do not hard-code a hosted vendor into domain logic. Every new dataset, model, library, or service requires a purpose and license note.

### 3.2 Recommended repository shape

The exact names may adapt to framework conventions, but keep these responsibilities separated:

```text
apps/
  web/                 Next.js reviewer and claimant application
  api/                 FastAPI modular monolith
    app/modules/       auth, vehicles, policies, claims, inspections, media,
                       analysis, risk, reviews, reports
  worker/              Celery entrypoint using backend domain services
ml/
  models/              model adapters and version metadata
  evaluation/          fixed evaluation manifests and metric scripts
  training/            optional training/fine-tuning code
infra/                 Docker and local service configuration
tests/                 cross-service integration and end-to-end tests
docs/                  product, plan, phases, decisions, and demo notes
```

The API and worker may share one Python package. This is still a modular monolith, not separate product microservices.

### 3.3 Core data rules

- Use UUID/ULID-style non-sequential public identifiers.
- Store timestamps in UTC and keep the submitted timezone/source when relevant.
- Add `organization_id` to every tenant-owned entity and enforce it in queries and constraints.
- Use explicit status enums and validated state transitions.
- Use Alembic migrations; never rely on automatic schema creation outside disposable tests.
- Do not overwrite reviewer decisions, AI outputs, reports, or risk evaluations. Create versioned records.
- Store object keys and metadata in PostgreSQL; store media and generated binary artifacts in object storage.
- Keep original media immutable and private. Derived assets must reference their source media and producing model/job.
- Add `created_at`, `updated_at`, and where relevant `created_by`, `model_version`, `rule_version`, and `job_id`.

### 3.4 Background-job rules

- API requests enqueue expensive work and return a job/reference ID.
- Jobs must be idempotent or protected by an idempotency key.
- Persist `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, and `CANCELLED` states.
- Record attempt count, timestamps, progress, error category, safe error message, and correlation ID.
- Retry only transient failures with bounded exponential backoff.
- Do not retry corrupt media, invalid input, or deterministic model failures indefinitely.
- Partial pipeline failures must be visible; never silently publish an incomplete “successful” report.

### 3.5 Universal AI rules

- Separate part segmentation from damage segmentation.
- Every result must include confidence and model/threshold version.
- Keep raw model output separate from reviewer-corrected output.
- Use `UNKNOWN` when input quality, model confidence, viewpoint compatibility, or alignment is insufficient.
- Treat metadata, ELA, provenance, and manipulation detectors as independent signals.
- Missing metadata/provenance is neutral.
- LLMs may only use supplied structured claim evidence and must return schema-validated output.
- Never emit “fraud detected” or a “fraud probability.” Use evidence risk with reasons and human review.

### 3.6 Test layers required throughout

| Layer | Purpose |
|---|---|
| Unit | Business rules, validators, geometry/mask math, scoring, and utilities |
| API | Authentication, authorization, validation, state transitions, and error contracts |
| Integration | PostgreSQL, pgvector, object storage, Redis/Celery, and model adapters |
| Component | Forms, tables, viewers, error/loading/empty states, and accessibility |
| End to end | Critical user flows across browser, API, jobs, database, and storage |
| ML evaluation | Reproducible model/retrieval metrics on fixed manifests |
| Security regression | Tenant isolation, object access, role boundaries, unsafe uploads, and injection cases |

Tests must use synthetic, public-licensed, or consented data. Do not put real policyholder data in the repository or CI artifacts.

## 4. Phase 0 — Foundation

**Status:** In review  
**Suggested effort:** 2–4 weeks part-time  
**Depends on:** Nothing

**Implementation record (2026-09-02):** The Phase 0 application, migrations, local adapters, Docker Compose definition, responsive web workflow, seed data, and initial automated suites are implemented. Local API/web integration, production build, and desktop/mobile login E2E are verified. The phase remains `In review` until the full PostgreSQL/Redis/MinIO/Celery Docker stack is booted on a running Docker daemon and the remaining unchecked coverage items below are completed.

### 4.1 Goal

Create a secure, testable claims application and media-processing foundation without making AI conclusions.

### 4.2 Scope and features

#### Project and developer foundation

- [x] Create the web, API, worker, infrastructure, test, and documentation structure.
- [x] Add environment templates with no secrets or real credentials.
- [x] Add formatting, linting, type-checking, and test commands.
- [x] Add Docker Compose services for PostgreSQL/pgvector, Redis, object storage, API, worker, and web.
- [x] Add health/readiness checks and deterministic development seed data.
- [x] Publish OpenAPI documentation from FastAPI.

#### Authentication, roles, and tenancy

- [x] Implement sign-in, sign-out, password hashing, token/session expiry, and protected routes.
- [x] Support `ADMIN`, `REVIEWER`, and `CLAIMANT` behavior.
- [x] Scope every query and object key to an organization.
- [x] Prevent users from selecting or submitting a different organization ID.
- [x] Record important login and authorization events without logging secrets.

For the personal MVP, users may belong to one organization. Keep authorization logic centralized so multi-organization memberships can be added later without rewriting every module.

#### Core data model

- [x] `organizations`: name, type, status.
- [x] `users`: organization, identity, role, status.
- [x] `vehicles`: organization, registration, VIN, make, model, year, color.
- [x] `policies`: organization, vehicle, policy number, dates, status.
- [x] `claims`: organization, policy, incident details, description, status.
- [x] `inspections`: organization, vehicle, optional claim, type, status, submission timestamps.
- [x] `media`: organization, inspection, object key, MIME type, size, viewpoint, hashes, status.
- [x] `analysis_jobs`: organization, inspection/claim, type, state, progress, attempts, errors.
- [x] `reviews`: organization, claim, reviewer, decision, notes, version.
- [x] `audit_events`: actor, action, entity, entity ID, timestamp, safe change metadata.

Use uniqueness rules within an organization for policy number, registration number, and other business identifiers. Decide how incomplete/unknown VINs are represented instead of inserting fake values.

#### Core workflows and API

- [x] Vehicle create/list/detail/update and history shell.
- [x] Policy create/list/detail/update with vehicle and date validation.
- [x] Claim create/list/detail/update with explicit status transitions.
- [x] Inspection create/detail/submit for policy inception, renewal, claim, and post-repair types.
- [x] Private media upload initiation, completion, retrieval, and deletion-before-submission behavior.
- [x] Job enqueue/status/retry endpoints with role checks.
- [x] Review creation and history shell; AI-specific decisions arrive in later phases.
- [x] Consistent pagination, filters, error format, and API versioning.

#### Media ingestion

- [ ] Use private buckets and short-lived signed upload/download URLs.
- [x] Validate MIME by file content, extension, file size, dimensions, and decode success.
- [ ] Normalize orientation for derived processing without altering the original.
- [x] Compute SHA-256 while ingesting.
- [x] Store originals under non-guessable, organization-scoped keys.
- [ ] Create separate prefixes/records for thumbnails and future derived artifacts.
- [x] Prevent the same upload-completion request from creating duplicate media records.

#### Initial UI

- [x] Login and role-aware navigation.
- [x] Dashboard shell with real counts, not hard-coded production-looking data.
- [x] Vehicle and policy lists/forms/details.
- [x] Claims list, create form, and claim-detail shell.
- [x] Inspection creation and multi-image upload.
- [x] Upload progress, validation errors, job status, retry, empty, and failure states.
- [x] Basic vehicle-history timeline.

### 4.3 Things to make sure of

- Domain rules live in backend services, not only in UI validation.
- Policy dates, claim incident dates, and inspection relationships are validated.
- Submitted inspections cannot have original media silently replaced.
- Signed URLs do not grant cross-organization access.
- Failed jobs remain diagnosable without exposing stack traces to end users.
- Deleting draft media is allowed; deleting submitted evidence requires an auditable policy and is not implemented casually.
- All local services can be recreated from documented commands.

### 4.4 Required tests

- [ ] Unit tests for status transitions, date rules, identifiers, and object-key generation.
- [ ] API tests for CRUD validation, pagination, filters, and error contracts.
- [ ] Role and cross-organization authorization tests for every module.
- [x] Migration upgrade test against an empty database.
- [x] Upload tests for valid images, oversized files, MIME spoofing, corrupt images, duplicate completion, and unauthorized access.
- [ ] Job tests for success, transient retry, permanent failure, duplicate enqueue, and visible status.
- [ ] Frontend component tests for forms and all async states.
- [x] End-to-end test: create vehicle → policy → claim → inspection → upload → submit → view job state.

### 4.5 Out of scope in this phase

- Real segmentation, retrieval, OCR, forensics, risk scoring, LLM calls, and final reports.
- Video upload and camera guidance.
- Production billing, SSO, and external insurer integrations.

### 4.6 Deliverables

- Running local stack and setup instructions.
- Initial schema and migrations.
- Seeded demo organization/users.
- Working web/API/worker flow.
- Test report and documented known limitations.

### 4.7 Exit checklist

- [ ] A clean environment starts successfully from the documentation.
- [x] Each role sees only permitted actions and organization data.
- [ ] A baseline and claim inspection can be created and submitted with images.
- [x] Original media is private, immutable after submission, and retrievable through authorized access.
- [x] Job progress and failures are visible.
- [ ] Required automated tests pass.
- [x] No AI or risk result is simulated as if it were real.

## 5. Phase 1 — Damage Intelligence

**Status:** In review
**Suggested effort:** 4–7 weeks part-time
**Depends on:** Phase 0 complete

**Implementation note (2026-09-03):** The Phase 1 application and evaluation infrastructure is implemented with a deterministic synthetic-fixture adapter for repeatable end-to-end tests and an optional pinned CLIPSeg zero-shot adapter for exploratory baselining. Fixture output is labelled evaluation-only, while CLIPSeg output is labelled experimental until fixed-manifest metrics and representative failure cases are recorded. Phase 1 remains in review because representative dataset auditing and model-quality acceptance metrics are intentionally not claimed as complete.

### 5.1 Goal

Analyze a vehicle image and produce a versioned, reviewable report of vehicle parts and visible exterior damage.

### 5.2 Scope and features

#### Dataset and taxonomy preparation

- [ ] Audit candidate part/damage datasets for labels, image quality, duplicates, splits, and license terms.
- [x] Create a dataset/model license register before downloading or training.
- [x] Define a limited MVP taxonomy supported by available data.
- [x] Map external dataset labels into one canonical ClaimShield taxonomy.
- [x] Include `OTHER`/`UNKNOWN` behavior for unsupported or ambiguous cases.
- [ ] Create immutable train/validation/test manifests grouped to avoid the same vehicle leaking across splits where possible.

Start with common, visible classes rather than every class in `plan.md`. At minimum, aim to demonstrate dents, scratches, and cracks/broken components across major exterior parts. Expand only when evaluation data supports it.

#### Model integration

- [x] Define a common model-adapter interface for input, output masks, classes, confidence, and version.
- [x] Establish a pretrained segmentation baseline before fine-tuning.
- [x] Keep vehicle-part and damage models separate.
- [x] Record model weights checksum, source, license, preprocessing, input size, thresholds, and class mapping.
- [x] Run inference in a worker with CPU/GPU capability detection and an explicit timeout.
- [x] Store raw detections separately from reviewer corrections.
- [x] Use SAM 2 only for annotation/mask refinement assistance, not as the damage classifier. (SAM 2 is not included in the runtime.)

#### Analysis pipeline

- [x] Decode and normalize a derived working copy.
- [x] Run part segmentation.
- [x] Run damage segmentation.
- [x] Intersect each damage mask with candidate part masks.
- [x] Assign the best part only when overlap/confidence rules pass.
- [x] Calculate damage coverage as intersection area divided by visible part-mask area.
- [x] Calculate rule-based severity from damage type, coverage, region count, confidence, and part criticality.
- [x] Generate thumbnails, part masks, damage masks, and combined overlays.
- [x] Persist pipeline/model/threshold versions and timing.

#### Data/API additions

- [x] `model_versions` and/or an equivalent version registry.
- [x] `analysis_runs` for pipeline state and reproducibility.
- [x] `vehicle_part_detections` with class, confidence, mask key, and run.
- [x] `damage_detections` with class, confidence, mask key, severity, coverage, and run.
- [x] `finding_corrections` or versioned reviewer findings that preserve original outputs.
- [x] Inspection analysis start/status/results endpoints.
- [x] Reviewer correction and correction-history endpoints.

#### Reviewer UI

- [x] Original/overlay image viewer.
- [x] Toggle parts, damage, labels, and confidence.
- [x] Damage table with part, damage, severity, coverage, confidence, and source image.
- [x] Review actions to accept, reject, correct class/part/severity, and add notes.
- [x] Clear `UNKNOWN`, low-confidence, partial-analysis, and failed-analysis states.

### 5.3 Things to make sure of

- Never combine labels such as `scratched_left_door`; parts and damage stay separate.
- Coverage is based on the visible part mask, not the assumed physical surface area.
- Multiple overlapping part masks and damage spanning several parts are handled explicitly.
- Very low-quality or extreme close-up images may return `UNKNOWN` rather than a misleading part.
- Reviewer corrections do not overwrite raw model detections.
- Re-running with a new model creates a new analysis version.
- Generated overlays can always be traced to source media and model run.
- Do not describe rule-based severity as repair cost or structural severity.

### 5.4 Required tests and evaluation

- [x] Unit tests for mask intersection, overlap selection, coverage, clipping, empty masks, and multi-part ties.
- [x] Unit tests for severity boundaries and safety-critical part rules.
- [x] Model-adapter contract tests using fixed fixture outputs.
- [ ] Integration tests for GPU/CPU selection, persistence, object artifacts, timeout, retry, and partial failure.
- [x] API authorization tests for analysis and corrections.
- [ ] UI tests for overlay toggles, tables, low confidence, correction, and failure states.
- [x] End-to-end test: upload → analyze → view overlay → correct finding → view history.
- [ ] Record part mIoU/per-class IoU and damage mask mAP/IoU/Dice on fixed manifests.
- [ ] Record per-class precision/recall and confusion cases; do not report only aggregate metrics.

Set acceptance thresholds only after recording the first honest baseline. Document the selected thresholds and examples they fail on.

### 5.5 Out of scope in this phase

- Repair pricing, damage age, baseline comparison, duplicate search, manipulation decisions, and narrative consistency.
- Training several competing production models.
- Guaranteed detection of tiny scratches in uncontrolled photos.

### 5.6 Deliverables

- Canonical taxonomy and license register.
- Versioned model adapter and reproducible evaluation manifest.
- Damage-analysis worker pipeline.
- Reviewer damage viewer and correction workflow.
- Baseline metrics and limitations report.

### 5.7 Exit checklist

- [x] Fixed validation images produce repeatable, persisted results.
- [x] Each finding exposes evidence, confidence, and model version.
- [x] Damage-to-part mapping and severity rules pass unit tests.
- [x] Reviewers can correct every displayed finding and see the original result.
- [x] Failed or incomplete analysis cannot appear as a complete report.
- [ ] Metrics and known failure modes are documented.
- [ ] Required automated tests pass.

## 6. Phase 2 — Policy Baseline Comparison

**Status:** Not started  
**Suggested effort:** 3–6 weeks part-time  
**Depends on:** Phase 1 complete

### 6.1 Goal

Compare claim-time evidence with trusted earlier inspections and classify damage as `PRE_EXISTING`, `NEW`, `CHANGED`, or `UNKNOWN`.

### 6.2 Scope and features

#### Baseline management

- [ ] Mark accepted policy-inception/renewal inspections as eligible baselines.
- [ ] Preserve multiple baselines and select the latest valid baseline before the incident.
- [ ] Exclude rejected, incomplete, post-incident, or wrong-vehicle inspections.
- [ ] Display the complete inspection/damage timeline for the vehicle.

#### Viewpoint and candidate matching

- [ ] Store a controlled viewpoint vocabulary: front, corners, sides, rear, identity, damage close-up, and unknown.
- [ ] Start with user/reviewer-confirmed viewpoints.
- [ ] Add automatic viewpoint suggestions only when evaluated.
- [ ] Restrict baseline candidates to the same organization, vehicle, valid time range, and compatible viewpoints.
- [ ] Use DINOv2 embeddings to rank candidate images/parts.

#### Comparison pipeline

- [ ] Match visible parts between baseline and claim images.
- [ ] Use local features and geometric alignment/homography where confidence is sufficient.
- [ ] Transform/compare part and damage masks only inside reliable overlapping regions.
- [ ] Compare class, approximate location, overlap, coverage, and severity change.
- [ ] Store alignment quality and reasons for comparison failure.
- [ ] Produce versioned `PRE_EXISTING`, `NEW`, `CHANGED`, or `UNKNOWN` findings.
- [ ] Let reviewers confirm or correct matches and classifications.

#### Data/API/UI additions

- [ ] `baseline_selections` with reason and validity interval.
- [ ] `viewpoint_matches` with candidate scores and selected match.
- [ ] `damage_comparisons` with source/target findings, classification, confidence, method, and version.
- [ ] Baseline selection, comparison run/status, result, and correction endpoints.
- [ ] Side-by-side synchronized image viewer with overlays.
- [ ] Part-level comparison table and “why unknown” explanation.

### 6.3 Things to make sure of

- Never compare claim evidence with an inspection created after the incident.
- Do not treat the latest image as trusted merely because it is earlier.
- Same make/model is not same vehicle; vehicle ID and identity checks remain required.
- Pixel-perfect full-car registration is not required and should not be promised.
- Different angles, occlusion, replaced parts, paint/reflections, and low overlap must lower confidence or return `UNKNOWN`.
- “Changed” needs an explainable difference; it must not mean simply “model outputs differ.”
- Reviewer decisions are retained and can be used later for evaluation.

### 6.4 Required tests and evaluation

- [ ] Unit tests for eligible-baseline selection and incident-time boundaries.
- [ ] Unit tests for overlap/position comparison, confidence combination, and classification rules.
- [ ] Integration tests for embeddings, local matching, alignment artifacts, and versioned persistence.
- [ ] Negative tests for wrong vehicle, incompatible viewpoint, post-incident baseline, low overlap, and missing part.
- [ ] UI tests for synchronized comparison, no match, `UNKNOWN`, and reviewer correction.
- [ ] End-to-end vehicle-history test with baseline, renewal, claim, and corrected comparison.
- [ ] Evaluation set containing known unchanged, new, changed, and unmatchable cases.
- [ ] Report per-class accuracy/F1, false-new rate, false-pre-existing rate, and unknown rate.

### 6.5 Out of scope in this phase

- Exact physical damage-age estimation.
- Full 3D registration or accident reconstruction.
- Cross-vehicle and cross-insurer historical matching.

### 6.6 Deliverables

- Trusted-baseline selection logic.
- Versioned part/viewpoint comparison pipeline.
- Side-by-side historical comparison UI.
- Comparison evaluation report and failure examples.

### 6.7 Exit checklist

- [ ] The demo preserves a known pre-existing damage.
- [ ] The demo identifies a clearly new damage.
- [ ] A meaningful severity/coverage change can be labelled `CHANGED`.
- [ ] Unmatchable evidence reliably returns `UNKNOWN` with a reason.
- [ ] Time, vehicle, organization, and viewpoint constraints are tested.
- [ ] Reviewer overrides and original results are both visible.
- [ ] Required automated tests pass.

## 7. Phase 3 — Reused Image Intelligence

**Status:** Not started  
**Suggested effort:** 2–4 weeks part-time  
**Depends on:** Phase 1 complete; Phase 2 recommended

### 7.1 Goal

Detect exact files and common transformed/reused versions of historical claim evidence while controlling false positives.

### 7.2 Scope and features

#### Staged matching pipeline

- [ ] Stage 1: exact SHA-256 lookup.
- [ ] Stage 2: pHash/dHash lookup for resize, recompression, and mild color changes.
- [ ] Stage 3: DINOv2 embedding generation and pgvector Top-K search.
- [ ] Stage 4: LightGlue or equivalent local geometric verification for semantic candidates.
- [ ] Exclude self-matches and invalid/rejected media.
- [ ] Keep the MVP search boundary within one organization.
- [ ] Store every stage score, threshold version, candidate rank, and verification result.

#### Data/API/UI additions

- [ ] Add pHash and versioned embedding records/indexes.
- [ ] Add `historical_matches` with source, candidate, scores, method, state, and reviewer decision.
- [ ] Add index/backfill jobs that can safely resume.
- [ ] Add media/claim match result and reviewer decision endpoints.
- [ ] Add side-by-side match viewer with claim, vehicle, date, transformation scores, and reason.
- [ ] Allow reviewer confirmation/rejection without deleting the candidate record.

### 7.3 Things to make sure of

- A high semantic score alone is not proof of reuse; similar views of similar cars can collide.
- Exact matches may be legitimate within one inspection; context must be displayed.
- Crop and screenshot transformations may require geometric verification.
- Search results must never leak media or metadata across organizations.
- Index dimensions, distance metric, and normalization must match the selected embedding model.
- Re-indexing after a model change creates a new embedding version rather than mixing incompatible vectors.
- Favor high precision and reviewer confirmation for risk signals.

### 7.4 Required tests and evaluation

- [ ] Unit tests for SHA/pHash generation, distance calculations, threshold boundaries, and self-match exclusion.
- [ ] Integration tests for pgvector indexing/search, embedding version isolation, backfill resume, and authorization.
- [ ] Transformation fixtures: resize, JPEG recompression, crop, brightness, screenshot, mild edit, and unrelated lookalike.
- [ ] Geometric verification tests for valid overlap and semantic false positives.
- [ ] UI tests for exact, near, semantic, rejected, empty, and unavailable states.
- [ ] End-to-end test: historical claim upload → new transformed upload → match → reviewer decision.
- [ ] Measure Precision@K, Recall@K, ROC-AUC where appropriate, and false-positive rate by transformation.

### 7.5 Out of scope in this phase

- Cross-insurer federation.
- Person/device/workshop fraud networks.
- Treating an image match as a fraud decision.

### 7.6 Deliverables

- Versioned embedding/index pipeline.
- Staged matching service and worker jobs.
- Reviewer similarity viewer.
- Threshold evaluation report.

### 7.7 Exit checklist

- [ ] Exact duplicates are deterministic.
- [ ] Common transformed copies are found in the fixed test set.
- [ ] Similar but unrelated vehicle images do not routinely create strong verified matches.
- [ ] All results show stage scores and threshold/model versions.
- [ ] Organization isolation and vector-version isolation are tested.
- [ ] Reviewer decisions are retained.
- [ ] Required automated tests pass.

## 8. Phase 4 — Basic Media Forensics

**Status:** Not started  
**Suggested effort:** 2–4 weeks part-time for basic scope  
**Depends on:** Phase 0 complete; Phase 3 recommended

### 8.1 Goal

Extract and explain media-authenticity indicators without presenting weak forensic signals as proof.

### 8.2 Scope and features

#### Deterministic metadata and provenance

- [ ] Preserve raw EXIF and normalized metadata separately.
- [ ] Extract capture timestamp/timezone when present, device make/model, GPS, orientation, dimensions, software/editor, and encoding details.
- [ ] Compare capture time with incident time and inspection-session time using explicit tolerances.
- [ ] Compare optional GPS with incident/capture location only when consent and reliable data exist.
- [ ] Detect inconsistent device metadata across one inspection as a reviewable signal, not an accusation.
- [ ] Verify C2PA/Content Credentials when present and store the validation result.
- [ ] Treat valid provenance as positive evidence and missing provenance as neutral.

#### Research/experimental signals

- [ ] Generate ELA only as a secondary reviewer visualization.
- [ ] Define a model-adapter contract for optional learned manipulation localization.
- [ ] Label learned manipulation scores and heatmaps `EXPERIMENTAL` until evaluated on vehicle-domain data.
- [ ] Keep custom/synthetic forgery data manifests separate from production-like evaluation data.
- [ ] Do not add an experimental model score to final risk by default.

#### Data/API/UI additions

- [ ] `media_metadata` or versioned raw/normalized metadata records.
- [ ] `forensic_signals` with type, value, severity, confidence, evidence, method version, and review state.
- [ ] `provenance_checks` and derived ELA/heatmap artifact references.
- [ ] Forensic run/status/result and reviewer-correction endpoints.
- [ ] Metadata table, clear signal explanation, provenance status, and experimental heatmap viewer.

### 8.3 Things to make sure of

- Missing or stripped metadata is common and must not raise risk by itself.
- EXIF timestamps may lack timezone or be incorrectly configured; represent uncertainty.
- Re-encoding by messaging apps can remove/change metadata without malicious intent.
- ELA varies with compression and must never be called proof of editing.
- A software/editor tag can indicate normal processing.
- Raw metadata may contain sensitive GPS/device information; restrict display and logging.
- Model and dataset licenses must be verified before using TruFor or any alternative.

### 8.4 Required tests and evaluation

- [ ] Fixture tests for valid EXIF, no EXIF, malformed EXIF, timezone ambiguity, GPS, editor tags, screenshots, and recompressed images.
- [ ] Unit tests for time tolerance, GPS distance, device-consistency, neutrality, and signal severity rules.
- [ ] Integration tests for metadata persistence, artifact generation, corrupt input, and partial failure.
- [ ] Authorization/privacy tests for GPS, raw metadata, and forensic artifacts.
- [ ] UI tests distinguishing verified, neutral, anomalous, unavailable, and experimental states.
- [ ] End-to-end test: upload fixtures → extract → display → reviewer correction.
- [ ] If a learned detector is included, record image ROC-AUC, pixel F1/IoU, and false-positive rate on separate in-domain and generic sets.

### 8.5 Out of scope in this phase

- Claiming reliable detection of every Photoshop or generative edit.
- Using ELA as a binary manipulation classifier.
- Training a commercial-grade vehicle forgery model.

### 8.6 Deliverables

- Deterministic metadata/provenance pipeline.
- Explainable forensic-signal UI and reviewer correction.
- Optional experimental adapter isolated from trusted logic.
- Forensic limitations and privacy note.

### 8.7 Exit checklist

- [ ] Known metadata conflicts are detected and explained.
- [ ] Missing metadata/provenance produces no penalty.
- [ ] Every signal points to exact stored evidence and method version.
- [ ] Experimental output is unmistakably labelled and excluded from default risk.
- [ ] Sensitive metadata access is authorized and tested.
- [ ] Required automated tests pass.

## 9. Phase 5 — Guided Capture and Vehicle Identity

**Status:** Not started  
**Suggested effort:** 3–5 weeks part-time  
**Depends on:** Phases 0 and 1 complete

### 9.1 Goal

Collect standardized, complete, and identity-linked inspection evidence through a mobile-first web flow.

### 9.2 Scope and features

#### Capture session

- [ ] Create an expiring, claim/inspection-scoped capture invitation or authenticated claimant session.
- [ ] Show consent, privacy purpose, required evidence, and safe capture guidance.
- [ ] Support resume after refresh/network interruption without duplicate records.
- [ ] Bind uploads to capture session, inspection, vehicle, and organization.
- [ ] Record server timestamps, client timestamps as untrusted context, and optional consented location.

#### Required views

- [ ] Policy inspection: front, front-left, left, rear-left, rear, rear-right, right, front-right, VIN, plate, and odometer.
- [ ] Claim inspection: compatible overview views plus required damage close-ups.
- [ ] Track required, accepted, rejected, missing, and retake states.
- [ ] Allow reviewer-configured additional evidence requests.

#### Immediate quality validation

- [ ] Resolution, aspect ratio, decode, and file-size checks.
- [ ] Blur and brightness/exposure checks with device-friendly thresholds.
- [ ] Vehicle-presence and visibility checks.
- [ ] Occlusion and required-viewpoint confidence where supported.
- [ ] Clear retake guidance that states what failed.
- [ ] Server-side revalidation after client-side feedback.

#### Vehicle identity

- [ ] Plate detector → crop → OCR → normalization → policy comparison.
- [ ] VIN detector/crop → OCR → uppercase normalization → 17-character validation → policy comparison.
- [ ] Exclude invalid VIN characters such as I, O, and Q; do not assume every market uses identical check-digit behavior.
- [ ] Make regional plate normalization configurable and benchmark it on representative local examples.
- [ ] Always allow claimant/reviewer correction while retaining OCR output and confidence.
- [ ] Emit an identity mismatch signal, not a fraud decision.

#### UI/API/data additions

- [ ] `capture_sessions`, `capture_requirements`, and state/expiry records.
- [ ] `quality_checks` with metric, threshold version, result, and message.
- [ ] `identity_extractions` with raw OCR, normalized value, confidence, match state, and correction.
- [ ] Capture invitation/session, upload, validation, retake, resume, and submit endpoints.
- [ ] Mobile-first stepper with camera permission, progress, offline/network errors, review, and submission confirmation.

### 9.3 Things to make sure of

- Client-side checks improve UX; server-side checks remain authoritative.
- Camera permission denial, unsupported browsers, low memory, and weak networks have recovery paths.
- Do not permanently store location without explicit consent and a documented need.
- Client timestamps are not trusted evidence on their own.
- OCR mismatch must show both extracted and expected values and permit correction.
- Camera-first capture is preferred, but controlled gallery upload may remain available for development/accessibility.
- Hash originals on ingestion and prevent post-submission replacement.

### 9.4 Required tests and evaluation

- [ ] Unit tests for capture requirement completion, expiry, VIN validation, and plate normalization.
- [ ] Quality-check fixture tests for blur, darkness, overexposure, low resolution, occlusion, and non-vehicle images.
- [ ] OCR evaluation with clean, angled, reflective, blurred, and partially occluded plate/VIN images.
- [ ] API tests for expired/used invitations, wrong inspection, duplicate upload, retake replacement before submission, and post-submission immutability.
- [ ] Mobile component tests for permission denied, retry, resume, progress, and correction.
- [ ] Playwright tests on representative mobile viewport/browser profiles.
- [ ] End-to-end test: invitation → capture sequence → retake → OCR correction → submit → reviewer view.
- [ ] Record retake rate, completion rate, per-check rejection rate, and OCR exact/normalized match accuracy.

### 9.5 Out of scope in this phase

- Native React Native application.
- Guided walk-around video and randomized liveness actions.
- Guaranteed make/model/year classification from appearance.

### 9.6 Deliverables

- Mobile-first capture PWA flow.
- Versioned quality checks.
- Plate/VIN extraction and correction workflow.
- Capture evaluation report and supported-browser note.

### 9.7 Exit checklist

- [ ] A claimant can complete both policy and claim capture flows on a phone.
- [ ] Missing/poor required views block submission with useful guidance.
- [ ] Interrupted sessions resume safely.
- [ ] OCR results are reviewable and correctable.
- [ ] Session, vehicle, inspection, and organization bindings cannot be bypassed.
- [ ] Submitted originals are immutable and hashed.
- [ ] Required automated tests pass.

## 10. Phase 6 — Claim Intelligence, Risk, and Reporting

**Status:** Not started  
**Suggested effort:** 3–6 weeks part-time  
**Depends on:** Phases 1–5 complete at their required scope

### 10.1 Goal

Combine structured evidence into an explainable reviewer workflow and generate the final end-to-end ClaimShield MVP report.

### 10.2 Scope and features

#### Narrative extraction

- [ ] Define a strict incident schema: collision type, claimant vehicle state, impact direction, expected regions, uncertainty, and source text.
- [ ] Use an LLM provider adapter with schema-constrained output, timeout, retry, and safe fallback.
- [ ] Store prompt/template version, model/provider version, raw response where permitted, parsed output, and validation errors.
- [ ] Let reviewers view and correct the structured narrative.
- [ ] Treat prompt content as untrusted input and prevent it from overriding system rules.

#### Consistency engine

- [ ] Compare expected regions with detected damage locations.
- [ ] Consider pre-existing/new status, identity, metadata, and duplicate matches.
- [ ] Produce individual consistency findings rather than one unexplained score.
- [ ] Include “insufficient visual evidence” and “partially consistent” outcomes.
- [ ] Keep deterministic comparison rules separate from LLM wording.

#### Evidence-risk engine

- [ ] Create a registry of versioned signal types and rule definitions.
- [ ] Support signals such as verified historical match, identity mismatch, prior-damage overlap, deterministic metadata conflict, narrative inconsistency, and poor capture quality.
- [ ] Store raw signal value, normalized contribution, weight, reason, evidence references, rule version, and review state.
- [ ] Calculate a bounded score and map it to `LOW`, `MEDIUM`, or `HIGH` using versioned thresholds.
- [ ] Treat missing/unavailable signals as neutral, not zero-confidence guilt.
- [ ] Recalculate into a new risk version when evidence, rules, or reviewer-confirmed findings change.
- [ ] Keep experimental manipulation scores out of default risk unless separately approved and validated.

Initial weights in `plan.md` are starting hypotheses, not validated probabilities. They must be configurable and labelled as rule-based prioritization.

#### Grounded AI summary/assistant

- [ ] Build a structured evidence package with stable finding IDs and media references.
- [ ] Ask the LLM only to summarize or answer from that package.
- [ ] Require each generated statement/reason to reference supporting finding IDs.
- [ ] Validate generated output and reject unsupported references.
- [ ] Provide deterministic fallback summaries when the LLM is unavailable.
- [ ] Never let the assistant approve/reject a claim or introduce evidence not stored in the system.

#### Reviewer workflow

- [ ] Dashboard cards and claim table with status, risk, filters, sorting, pagination, and assignment.
- [ ] Claim header with policy, vehicle, incident, analysis version, risk, and processing status.
- [ ] Risk summary with individual signals and evidence links.
- [ ] Damage viewer/table, baseline comparison, historical matches, forensics, identity, and narrative sections.
- [ ] Review actions: accept/correct finding, request more evidence, refer for physical inspection, refer for investigation, complete review.
- [ ] Explicit state machine preventing invalid transitions and recording actor/time/reason.

#### Reports and audit

- [ ] Generate versioned JSON report as the canonical machine-readable output.
- [ ] Generate a human-readable PDF from the same report data.
- [ ] Include evidence IDs, findings, confidence, versions, limitations, reviewer decision, and generation time.
- [ ] Never alter an issued report; generate a new version after changes.
- [ ] Log analysis, correction, risk, report, and review events in the audit trail.

### 10.3 Things to make sure of

- Risk is called “Evidence Risk,” never “Fraud Probability.”
- A high score means manual review is recommended, not that fraud occurred.
- Every risk contribution is traceable to evidence and a rule version.
- Reviewer-corrected findings and model findings remain distinguishable.
- Narrative inconsistencies account for missing views and uncertain detections.
- LLM failures do not block deterministic evidence review or report generation.
- Reports do not expose internal storage keys, secrets, hidden prompts, or unrelated customer data.
- Reanalysis does not silently change a previously reviewed/issued report.

### 10.4 Required tests and evaluation

- [ ] Schema tests for valid, ambiguous, empty, malicious, and multilingual/poorly written narratives.
- [ ] Prompt-injection and unsupported-evidence tests.
- [ ] Unit tests for each consistency and risk rule, weight, threshold boundary, neutral missing signal, and version recalculation.
- [ ] Property/invariant tests ensuring score bounds and deterministic repeated results.
- [ ] Integration tests for LLM timeout/failure, fallback summary, report generation, and audit events.
- [ ] Authorization tests for assignment, review actions, evidence access, and report access.
- [ ] UI tests for all claim states, filters, evidence navigation, reviewer correction, and unavailable modules.
- [ ] PDF/JSON consistency test using the canonical report data.
- [ ] End-to-end final demo test from baseline capture to completed human review.
- [ ] Grounded-summary evaluation: every claim in the summary maps to an existing finding ID.
- [ ] Record reviewer disagreement rate and risk-signal false-positive examples on the demo/evaluation set.

### 10.5 Out of scope in this phase

- Learning risk weights from insurer outcomes without suitable labelled data.
- Autonomous decisions, payout, repair pricing, or open-ended assistant access to raw systems.
- Legal conclusions or definitive manipulation/fraud statements.

### 10.6 Deliverables

- Versioned narrative and consistency pipeline.
- Explainable rule-based risk engine.
- Complete reviewer dashboard and claim-detail workflow.
- Grounded summary with deterministic fallback.
- Versioned JSON/PDF report and audit trail.
- Scripted final demo dataset/story.

### 10.7 Exit checklist

- [ ] The complete baseline-to-claim demo runs without manual database edits.
- [ ] Every displayed and reported finding is traceable to evidence and a versioned method.
- [ ] Missing data remains neutral and uncertainty is visible.
- [ ] LLM output cannot introduce unsupported findings.
- [ ] Review state transitions and audit history are complete.
- [ ] JSON and PDF reports agree and are versioned.
- [ ] No screen or report says “fraud detected” or makes an automatic claim decision.
- [ ] Required automated tests pass.

## 11. Phase 7 — Evaluation, Security, and Release

**Status:** Not started  
**Suggested effort:** 2–4 weeks part-time, plus fixes  
**Depends on:** Phases 0–6 complete

### 11.1 Goal

Turn the working MVP into a reproducible, measurable, secure, and presentable release candidate.

### 11.2 Scope and features

#### Evaluation and robustness

- [ ] Freeze representative evaluation manifests and prevent test leakage.
- [ ] Record model, dataset, code, preprocessing, threshold, embedding, OCR, prompt, and risk-rule versions.
- [ ] Evaluate night, sunlight, rain, dirty vehicles, black/white/metallic paint, reflections, blur, compression, screenshots, low-end cameras, close-ups, partial vehicles, and aftermarket parts.
- [ ] Report per-class metrics and confidence intervals/sample counts where useful.
- [ ] Publish failure cases and unsupported conditions, not only successful examples.
- [ ] Define which results are demo-ready, experimental, or disabled.

Required metric families:

- Part segmentation: mIoU and per-class IoU.
- Damage segmentation: mask mAP, IoU/Dice, per-class precision/recall.
- Severity: macro/weighted F1, confusion matrix, ordinal disagreement.
- Baseline comparison: class accuracy/F1, false-new, false-pre-existing, and unknown rates.
- Duplicate retrieval: Precision@K, Recall@K, false-positive rate by transformation.
- Forensics: deterministic rule accuracy; learned detector ROC-AUC/pixel F1/IoU only if included.
- Capture/OCR: completion/retake rates and normalized plate/VIN accuracy.
- Product: processing time, job failure rate, reviewer corrections/disagreement, and report generation time.

#### Security and privacy

- [ ] Write a lightweight threat model covering accounts, tenant boundaries, uploads, signed URLs, jobs, AI inputs, reports, and admin actions.
- [ ] Review authentication/session expiry, password reset path, authorization, CSRF/CORS, rate limits, and brute-force controls.
- [ ] Validate upload parsing, decompression limits, filenames, MIME, dimensions, and object keys.
- [ ] Confirm private buckets, short-lived signed URLs, encryption in transit, and secret handling.
- [ ] Define data retention, consent, location/EXIF treatment, deletion, and backup behavior for demo data.
- [ ] Redact sensitive data from logs, traces, errors, screenshots, test reports, and LLM requests.
- [ ] Verify audit events cannot be casually edited through application APIs.
- [ ] Run dependency and container vulnerability scans and document accepted risks.

#### Reliability and observability

- [ ] Add structured logs with request/job correlation IDs.
- [ ] Add metrics for API latency/errors, queue depth, job duration/failures, model timing, storage errors, and report failures.
- [ ] Add health/readiness checks that reflect dependency state.
- [ ] Define bounded retries, dead-letter/manual retry handling, and stale-job recovery.
- [ ] Test database backup and restore using non-sensitive demo data.
- [ ] Define model/artifact availability behavior and a graceful degraded mode.

#### Release and demonstration

- [ ] CI runs formatting, linting, type checks, migrations, unit, integration, frontend, and selected E2E tests.
- [ ] Build reproducible web/API/worker images.
- [ ] Document local and demo deployment, environment variables, storage setup, migrations, worker/GPU setup, seeding, backup, and rollback.
- [ ] Create a deterministic demo scenario with one vehicle across baseline and claim events.
- [ ] Include known limitations, ethical use, and human-review disclaimer.
- [ ] Prepare screenshots/demo steps only from synthetic or consented data.

### 11.3 Things to make sure of

- Security checks cover organization isolation at database, API, signed URL, vector search, and report levels.
- Evaluation sets are not tuned repeatedly until they become training data.
- Demo fixtures intentionally include expected success, uncertainty, and failure behavior.
- A GPU outage or LLM outage degrades visibly instead of producing fabricated results.
- Deployment does not require Kubernetes or split the modular monolith.
- Backups are not considered valid until restoration is tested.

### 11.4 Required tests

- [ ] Full regression suite and fresh-database migration test.
- [ ] Cross-organization and cross-role access matrix.
- [ ] Signed-URL expiry/reuse and direct object-access tests.
- [ ] Rate-limit, malformed input, prompt injection, unsafe upload, and oversized/decompression tests.
- [ ] Concurrent upload, duplicate submission, duplicate job, retry, worker restart, and stale-job tests.
- [ ] Backup/restore and report-version recovery tests.
- [ ] Performance tests for realistic image batch size and concurrent reviewer usage.
- [ ] Accessibility checks for keyboard use, labels, contrast, error messages, tables, dialogs, and mobile capture.
- [ ] Clean-machine deployment and complete scripted demo rehearsal.

### 11.5 Deliverables

- Release candidate and reproducible deployment instructions.
- Evaluation/robustness report.
- Threat model, privacy/retention note, and security checklist.
- Operations/runbook and backup/restore procedure.
- Demo seed data, script, and known-limitations document.

### 11.6 Exit checklist

- [ ] Clean setup, migration, seed, test, and demo instructions work.
- [ ] No critical tenant-isolation, authorization, data-loss, or secret-exposure issue remains.
- [ ] Backup and restore are verified.
- [ ] Required evaluation metrics and limitations are published.
- [ ] The application handles dependency/model/LLM failure safely.
- [ ] The final demo includes human correction and uncertainty, not only ideal predictions.
- [ ] CI and required release tests pass.
- [ ] The personal-project MVP is complete.

## 12. Phase 8 — Enterprise and Research Extensions

**Status:** Deferred  
**MVP requirement:** None

Do not start Phase 8 until the Phase 7 release criteria pass and a specific use case justifies the added complexity.

Potential extensions:

- Domain-trained vehicle manipulation and generative-edit localization.
- Guided video, random visual liveness actions, and video damage tracking.
- Make/model/color/body-type consistency signals.
- Repair estimate, parts catalog, invoice OCR, and workshop estimate validation.
- Device, vehicle, image, claimant, and repair-shop relationship graphs.
- Cross-claim anomaly detection and SIU investigation dashboard.
- Cross-organization matching with explicit contracts, consent, privacy, and legal controls.
- Fleet, leasing-return, rental, used-car, and post-repair workflows.
- SSO, advanced RBAC, configurable workflows, webhooks, enterprise APIs, and insurer integrations.
- Model monitoring, feedback-driven retraining, shadow deployment, and calibrated risk models using confirmed outcomes.

Before implementing any extension, create a separate scoped phase containing its data authority, privacy impact, success metrics, human controls, deployment cost, and rollback plan.

## 13. Cross-phase definition of done

A phase is complete only when all applicable statements are true:

- [ ] Its required features work end to end through the real UI/API/job/data path.
- [ ] Database changes have reviewed, reversible migrations.
- [ ] Inputs, authorization, organization scoping, and failure states are tested.
- [ ] Original evidence remains immutable and derived artifacts are traceable.
- [ ] AI, threshold, embedding, prompt, rule, and report versions are recorded where applicable.
- [ ] Confidence, uncertainty, and `UNKNOWN` behavior are visible to reviewers.
- [ ] Reviewer corrections preserve the original output and audit history.
- [ ] No experimental result is presented as validated evidence.
- [ ] Required unit, integration, component, end-to-end, evaluation, and security tests pass.
- [ ] New dependencies/models/datasets have documented purpose and licensing.
- [ ] Documentation, API contracts, environment examples, and demo data match actual behavior.
- [ ] No sensitive or unlicensed data has entered source control, CI, logs, screenshots, or reports.
- [ ] The phase exit checklist is checked and its evidence is recorded before the next phase begins.
