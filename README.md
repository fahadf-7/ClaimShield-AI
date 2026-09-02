# ClaimShield AI

ClaimShield AI is a human-in-the-loop motor-insurance evidence workspace. Phase 0 establishes the product foundation: tenant-scoped records, private media ingestion, visible background-job states, and the reviewer web workflow. It deliberately performs no damage, fraud, or risk analysis yet.

## Phase 0 capabilities

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

## Test the Phase 0 workflow

1. Open `http://localhost:3000/login` and sign in as the seeded reviewer.
2. Open **Vehicles** and register a passenger vehicle.
3. Open **Policies** and create an active policy for that vehicle.
4. Return to the vehicle detail page and select **New baseline**.
5. Upload at least one JPEG, PNG, or WebP image of 640×480 or larger.
6. Select **Submit and lock evidence**. Confirm the inspection becomes `READY` and the validation job becomes `SUCCEEDED`.
7. Try uploading again to the submitted inspection. The API must reject replacement because originals are immutable.
8. Open **Claims**, create a claim whose incident date is within the policy period, and open it.
9. Create a claim inspection, upload evidence, and submit it.
10. Return to the vehicle detail page and confirm both inspections appear in its timeline.

The successful Phase 0 job message explicitly says that no AI analysis was performed.

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

## Important Phase 0 limitations

- SQLite/local storage/eager jobs are development adapters only.
- There is no computer-vision, retrieval, forensic, narrative, or risk output in this phase.
- Claimant capture invitations, automated image-quality scoring, OCR, and guided angles begin in later phases.
- The current token implementation is suitable for this controlled prototype; production deployment requires hardened session management, reset/revocation flows, rate limits, and a security review.

See [the implementation roadmap](docs/phases.md), [product overview](docs/product_overview.md), and [technical plan](docs/plan.md).
