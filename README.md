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
uvicorn backend.app.main:app --reload
```

Open <http://127.0.0.1:8000/docs>. The default database is a local SQLite file. Docker Compose
uses PostgreSQL when Docker is available:

```powershell
docker compose up --build
```
The dashboard is available at <http://127.0.0.1:5173>.

Database migrations run automatically during the API container startup:

```powershell
docker compose exec api alembic upgrade head
docker compose exec api python scripts/populate_sample_data.py
```

Set `DEPLOYGUARD_API_KEY` to protect mutating API endpoints. When unset, local development
remains open. Send it as `X-API-Key` for protected mutations.

## API overview

- `GET /health`
- `POST /api/pipelines/analyze`
- `POST /api/pipelines/executions`
- `GET /api/pipelines`
- `POST /api/tests/reports`
- `GET /api/tests`
- `POST /api/infrastructure/analyze`
- `POST /api/deployments/risk`
- `GET /api/dashboard`

## Development

```powershell
pytest
ruff check .
mypy backend
python scripts/populate_sample_data.py
```

No AWS credentials or network services are required.

