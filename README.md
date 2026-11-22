# DeployGuard

DeployGuard is a local-first CI/CD intelligence and deployment reliability platform.

It analyzes GitHub Actions workflows and execution results, parses JUnit and Robot Framework
reports, identifies flaky tests, inspects Terraform configurations, and calculates transparent
deployment risk scores.

## Quick start

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn backend.app.main:app --reload
```

Open <http://127.0.0.1:8000/docs>. The default database is a local SQLite file. Docker Compose
uses PostgreSQL when Docker is available:

```powershell
docker compose up --build
```
Compose applies migrations before API startup and persists PostgreSQL data in a named volume.
The dashboard is available at <http://127.0.0.1:5173>; API and database ports bind to localhost.
Copy `.env.example` to `.env` to configure the local API key, PostgreSQL password/host port, or
frontend API URL. Change `POSTGRES_PORT` if host port 5432 is already occupied. The default
credentials are for local development only.
When upgrading an older Compose setup, back up and migrate its anonymous PostgreSQL volume before
starting with the new named volume; Docker does not copy data between those volumes automatically.

Seed the local database with synthetic demo data:

```powershell
docker compose exec api python scripts/populate_sample_data.py
```

Set `DEPLOYGUARD_API_KEY` to protect mutating API endpoints. When unset, development remains open.
`ENVIRONMENT=production` requires an API key, but this single-key check is not complete
authentication: read endpoints remain unauthenticated and role-based authorization is not
implemented. Send the key as `X-API-Key` for protected mutations.

## API overview

- `GET /health`
- `GET /health/live`
- `GET /health/ready`
- `POST /api/pipelines/analyze`
- `POST /api/pipelines/executions`
- `GET /api/pipelines/{pipeline_id}/executions`
- `GET /api/pipelines`
- `POST /api/tests/reports`
- `GET /api/tests`
- `POST /api/infrastructure/analyze`
- `POST /api/deployments/risk`
- `GET /api/dashboard`
- `POST /api/notifications/rules`
- `GET /api/notifications`

## Development

```powershell
pytest
ruff check .
mypy backend
python scripts/populate_sample_data.py
```

No AWS credentials or network services are required.

The dashboard uses API data and displays an unavailable state if the API cannot be reached.
Mutating routes accept an optional `DEPLOYGUARD_API_KEY`; configure it for shared or deployed
environments. When `ENVIRONMENT=production`, the API key is required; it does not protect read
endpoints. Role-based authorization and webhook event delivery are not implemented yet.

See [Project Status](docs/PROJECT_STATUS.md) for verified functionality and limitations and
[Repository Audit](docs/REPOSITORY_AUDIT.md) for evidence-based findings and remaining priorities.
See the [Engineering Backlog](docs/engineering-backlog/README.md) for clearly typed future tasks.

