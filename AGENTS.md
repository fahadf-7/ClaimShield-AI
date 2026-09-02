# ClaimShield AI — Agent Rules

## Project identity

- The product name is **ClaimShield AI**. Use this spelling in product copy and documentation.
- ClaimShield is a human-in-the-loop motor-insurance evidence platform, not an autonomous fraud or claim-decision system.
- Read `docs/product_overview.md`, `docs/plan.md`, and `docs/phases.md` before making architectural or product changes.
- `docs/phases.md` is the implementation source of truth. `docs/plan.md` is the broader technical reference.

## Scope and delivery

- Work on one phase at a time and satisfy its completion gate before starting the next phase.
- Do not add future or out-of-scope features unless explicitly requested.
- Prefer a complete, testable vertical slice over several unfinished capabilities.
- Keep the initial product focused on passenger vehicles, still images, one organization, and explainable reviewer workflows.
- Record material scope or architecture decisions in the relevant document.

## Architecture

- Keep a modular monolith: Next.js frontend, FastAPI backend, PostgreSQL/pgvector, S3-compatible storage, and Redis-backed background jobs.
- Keep business modules separate: auth, organizations, vehicles, policies, claims, inspections, media, AI analysis, risk, reviews, and reports.
- Run expensive or long AI work in background jobs; API requests must not wait for full inference pipelines.
- Keep original uploads immutable. Store derived masks, overlays, heatmaps, and reports separately.
- Make every tenant-owned database query organization-scoped.
- Use database migrations for schema changes and version model outputs, risk rules, and generated reports.
- Do not introduce microservices, Kubernetes, or a separate vector database without a demonstrated need.

## AI and insurance safety

- Never label a claim as fraudulent or automatically approve, reject, or price a claim.
- Use `Evidence Risk: Low/Medium/High` with specific supporting signals and a human-review recommendation.
- Every AI result must expose confidence, evidence, model/rule version, and a reviewer correction path.
- Return `UNKNOWN` when evidence is insufficient; do not force a confident classification.
- Treat missing metadata or missing provenance as neutral, not suspicious.
- Treat ELA and learned manipulation results as indicators, never proof.
- LLMs may parse narratives and summarize stored structured findings; they must not invent evidence or independently decide risk.
- Preserve reviewer corrections for audit and future evaluation.

## Engineering quality

- Inspect existing code and nearby tests before editing.
- Keep changes small, typed, and consistent with the existing structure.
- Validate external inputs and use explicit error states; do not silently ignore failed AI jobs.
- Never commit secrets, credentials, customer media, or sensitive policyholder data.
- Add or update tests for changed behavior and run the relevant checks before declaring work complete.
- New datasets, models, or dependencies require a documented purpose and a license check before use.
- Use synthetic or consented data during development.
- Do not weaken security, auditability, tenancy isolation, or human-review controls to simplify a demo.

## Definition of done

A feature is complete only when its data flow works end to end, failures are visible, relevant tests pass, reviewer-facing evidence is understandable, and the phase documentation remains accurate.
