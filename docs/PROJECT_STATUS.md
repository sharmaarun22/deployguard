# Project Status

## Implemented

- FastAPI application with health, pipeline, test, infrastructure, risk, and dashboard endpoints.
- SQLite local persistence with PostgreSQL support in Docker Compose.
- GitHub Actions workflow YAML parsing and validation.
- Failure classification with evidence and uncertainty-aware unknown results.
- Pipeline execution history with optional source-run idempotency keys.
- JUnit XML and Robot Framework XML parsing.
- Suite-scoped flaky-test detection that excludes skipped runs, and slow-test reporting.
- Terraform static analysis and plan JSON analysis.
- Deterministic configurable deployment-risk scoring that reports missing evidence.
- Responsive React dashboard backed by the dashboard API.
- Alembic schema migrations; Compose applies migrations before API startup.
- Optional API-key protection on mutating routes.
- Notification rule storage and paginated in-app notification listing.
- HTTPS webhook URL validation; outbound delivery is intentionally not implemented.
- Compose health check, localhost-only ports, named PostgreSQL volume, and build-time API URL.
- Synthetic workflow, XML, Terraform, and log fixtures.
- Mermaid architecture documentation and an initial ADR.
- 90 categorized engineering-backlog tasks.
- Backend unit and API integration tests; frontend component tests.
- Ruff, MyPy, Pytest, Docker, and GitHub Actions configuration.

## Verified in this session

- Backend: Ruff passes, strict MyPy passes, and all 40 tests pass in the Linux container.
- SQLite migrations: fresh upgrade and unversioned legacy-schema upgrade preserve the existing
  pipeline row and create the execution-history table and index.
- PostgreSQL Compose: both database and API report healthy; Alembic is at `0002_execution_history_utc`.
- Runtime smoke: health/readiness endpoints, frontend HTTP 200, execution history, idempotent
  ingestion, and failure classification all verified. The smoke-test database rows were removed.
- Frontend: lint, 2 component tests, TypeScript production build, and Vite build pass.
- Docker Compose configuration parses successfully.
- Host port 5432 was occupied, so Compose was started on localhost port 5433. At the user's request,
  the old anonymous volume was deleted after confirming no container used it; the new named volume
  is active.

## Known limitations

- Authentication is a single optional API-key model; role-based authorization is pending.
- Webhook event dispatch and durable retry scheduling are not wired into pipeline events.
- Notification rules are stored but are not yet evaluated against event streams.
- Webhook validation does not resolve DNS; URLs are never sent by the current application.
- Terraform configuration analysis uses regular expressions, not a full HCL parser.
- Static findings must not be interpreted as live AWS observations.
- PostgreSQL timestamps are timezone-aware; SQLite does not preserve timezone metadata when values
  are read back, so UTC API serialization still needs explicit tests.
- PostgreSQL migration behavior passed a local Compose smoke test but is not yet automated in CI.
- Production deployment still needs secrets management, RBAC, TLS termination, and operational
  monitoring; Compose defaults are local-development settings.
- GitHub Actions full workflow integration and live provider integrations remain future work.

## Verification commands

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
pytest
ruff check .
mypy backend
uvicorn backend.app.main:app --reload
```

Container validation:

```powershell
docker compose up --build
docker compose exec api python scripts/populate_sample_data.py
```

See [Repository Audit](REPOSITORY_AUDIT.md) for the evidence-based assessment and remaining
priorities.
