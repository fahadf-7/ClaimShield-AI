# ClaimShield AI

ClaimShield AI is a human-in-the-loop motor-insurance evidence workspace. Phase 1 adds versioned vehicle-part and visible-damage analysis to the Phase 0 foundation. Results are evidence for a reviewer: the product does not label fraud or make claim decisions.

## Current capabilities

- Secure demo authentication with admin, reviewer, and claimant roles.
- Organization-scoped vehicles, policies, claims, inspections, media, jobs, reviews, and audit events.
- Vehicle, policy, and claim creation and review pages.
- Policy-inception and claim inspection workflows.
- JPEG/PNG/WebP validation, SHA-256 hashing, private storage, and immutable submitted originals.
- Idempotent submission with a Redis/Celery foundation-validation job.
- Visible queued/running/succeeded/failed job states.
- Responsive reviewer console and mobile-friendly forms.
- PostgreSQL/pgvector, Redis, MinIO, FastAPI, worker, and Next.js Docker services.
- Alembic migrations, API tests, frontend tests, and CI configuration.
- Separate vehicle-part and damage segmentation adapters with an `UNKNOWN` path.
- Damage-to-part mapping, visible-part coverage, and deterministic rule-based severity.
- Immutable derived masks, overlays, thumbnails, model metadata, checksums, and run timings.
- A reviewer analysis workspace with layer toggles, version selection, warnings, and correction history.
- A deterministic synthetic adapter for repeatable development, plus an optional experimental CLIPSeg baseline.

## Demo accounts

The seed command creates synthetic development accounts. All use the password `ClaimShield123!`.

| Role | Email |
|---|---|
| Admin | `admin@claimshield.local` |
| Reviewer | `reviewer@claimshield.local` |
| Claimant | `claimant@claimshield.local` |

Never use these credentials or the development secret in a deployed environment.

## Option A: run the complete Docker stack

Prerequisites: Docker Desktop with the Linux container engine running.

```powershell
Copy-Item .env.example .env
# Replace SECRET_KEY and development passwords in .env before any shared deployment.
# Keep ANALYSIS_ADAPTER=fixture for the reproducible Phase 1 workflow.
docker compose up --build
```

Open:

- Web application: `http://localhost:3000`
- API documentation: `http://localhost:8000/docs`
- MinIO console: `http://localhost:9001`

The API container applies migrations and safely runs the idempotent seed before startup.

## Option B: run locally without Docker

This mode uses SQLite, local private storage, and eager background jobs. It is useful for personal development and automated tests; the Docker stack remains the target integration environment.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\apps\api\requirements-dev.txt
Copy-Item .\apps\api\.env.example .\apps\api\.env

Set-Location .\apps\api
..\..\.venv\Scripts\python.exe -m alembic upgrade head
..\..\.venv\Scripts\python.exe -m app.seed
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

In a second PowerShell terminal:

```powershell
Set-Location "D:\ClaimShield AI"
Copy-Item .\apps\web\.env.local.example .\apps\web\.env.local
npm install
npm run dev:web
```

## Test the Phase 1 workflow

1. Open `http://localhost:3000/login` and sign in as the seeded reviewer.
2. Open **Vehicles** and register a passenger vehicle.
3. Open **Policies** and create an active policy for that vehicle.
4. Open **Claims**, create a claim within the policy period, then create its claim inspection.
5. Generate the fixed synthetic image from the repository root:

   ```powershell
   .\.venv\Scripts\python.exe .\ml\evaluation\generate_phase1_fixture.py "$env:TEMP\claimshield-phase1-fixture.png"
   ```

6. Upload that PNG as the `FRONT` view and select **Submit and lock evidence**. Confirm the inspection becomes `READY`.
7. In **Damage intelligence**, select **Start analysis**. The fixture adapter should report `SUCCEEDED`, two vehicle parts, and three damage findings.
8. Toggle parts, damage, labels, and confidence; confirm the image layers update independently.
9. In the `DENT` row, select **Correct**, change the class to `SCRATCH`, choose a severity, add a note, and save. Confirm `CORRECT v1` appears while the raw `DENT` result remains visible.
10. Select **Run new version** and confirm the prior run remains selectable as version 1.

The fixture adapter recognizes only the generated color-coded image and is for deterministic testing, not real damage recognition. To explore real photos, set `ANALYSIS_ADAPTER=clipseg`; the pinned CLIPSeg model is downloaded on first use and its output remains explicitly experimental.

## Automated checks

Backend:

```powershell
Set-Location .\apps\api
..\..\.venv\Scripts\python.exe -m ruff check app tests
..\..\.venv\Scripts\python.exe -m alembic upgrade head
..\..\.venv\Scripts\python.exe -m pytest
```

Frontend:

```powershell
Set-Location "D:\ClaimShield AI"
npm run lint:web
npm run test:web
npm run build:web
```

Browser tests require the seeded API to be running and Microsoft Edge to be installed. Playwright starts the web app automatically when needed:

```powershell
npm run test:e2e
```

## Important Phase 1 limitations

- SQLite/local storage/eager jobs are development adapters only.
- The fixed synthetic fixture validates the software data flow, not model quality.
- Part mIoU and damage IoU/Dice/mAP on a representative licensed validation set are not established yet.
- The optional CLIPSeg zero-shot adapter is an exploratory baseline, not production-validated evidence.
- There is no repair pricing, damage-age, baseline comparison, duplicate search, forensic decision, narrative-consistency, or risk output in this phase.
- Claimant capture invitations, automated image-quality scoring, OCR, and guided angles begin in later phases.
- The current token implementation is suitable for this controlled prototype; production deployment requires hardened session management, reset/revocation flows, rate limits, and a security review.

See [the implementation roadmap](docs/phases.md), [product overview](docs/product_overview.md), and [technical plan](docs/plan.md).
