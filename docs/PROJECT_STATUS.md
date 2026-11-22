# Project Status

## Implemented

- FastAPI application with health, pipeline, test, infrastructure, risk, and dashboard endpoints.
- SQLite local persistence with PostgreSQL support in Docker Compose.
- GitHub Actions workflow YAML parsing and validation.
- Failure classification with evidence and uncertainty-aware unknown results.
- JUnit XML and Robot Framework XML parsing.
- Historical flaky-test detection and slow-test reporting.
- Terraform static analysis and plan JSON analysis.
- Deterministic configurable deployment-risk scoring.
- Synthetic workflow, XML, Terraform, and log fixtures.
- Mermaid architecture documentation and an initial ADR.
- 90 categorized engineering-backlog tasks.
- Backend unit and integration test sources.
- Ruff, MyPy, Pytest, Docker, and GitHub Actions configuration.

## Verified in this session

- Python 3.12.10 installed successfully.
- Editable package installation and test execution remain to be completed after packaging
  configuration was corrected.

- Docker Compose runs PostgreSQL, FastAPI, and the React dashboard.
- Alembic migration startup succeeds against the PostgreSQL database.
- API readiness and dashboard endpoints return successfully.

## Known limitations

- Authentication is a single optional API-key model; role-based authorization is pending.
- Alembic migration configuration is not yet created.
- Authentication and notification integrations are pending.
- Terraform analysis uses local regular-expression and JSON parsing, not a full HCL parser.
- Static findings must not be interpreted as live AWS observations.
- PostgreSQL and Docker validation depend on Docker availability.
- The repository Git metadata currently belongs to the parent `C:\Users\aruns\projects`
  directory; a dedicated DeployGuard repository is not yet initialized or configured with a
  remote.

## Verification commands

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
ruff check .
mypy backend
uvicorn backend.app.main:app --reload
```
