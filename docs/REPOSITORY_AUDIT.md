# DeployGuard Repository Audit

## Scope and outcome

This local audit reviewed the API, database models and migrations, workflow/test/infrastructure/risk
services, notification handling, Docker configuration, tests, status documentation, and backlog
entries that directly conflicted with the implementation. No remote Git operations, commits, pushes,
or PRs were performed.

The application is a useful local prototype, not a production-ready deployment gate. Confirmed
foundation defects were fixed and focused regression tests added. Large integration features remain
in the engineering backlog rather than being presented as complete.

## Capability assessment

| Area | Current status | Evidence |
|---|---|---|
| Workflow analysis | Accepts submitted YAML and reports a narrow set of structural/shell findings. It is not connected to a live GitHub repository or Actions API. | [pipeline.py](../backend/app/services/pipeline.py), [DG-INT-004](engineering-backlog/tasks.json) |
| Pipeline runs | Run results are now persisted separately from workflow analysis. Optional external IDs make ingestion idempotent per pipeline; no raw logs are retained. | [models.py](../backend/app/models.py), [main.py](../backend/app/main.py), [0002_execution_history_utc.py](../alembic/versions/0002_execution_history_utc.py) |
| Test intelligence | JUnit and Robot XML ingestion and historical heuristics exist. Flakiness is suite-scoped and skips do not count as completed attempts, but the score is not a statistical confidence estimate. | [test_intelligence.py](../backend/app/services/test_intelligence.py) |
| Infrastructure | Terraform checks are regex-based; plan JSON checks validate input shapes and identify selected changes. This is not a full HCL parser, cloud scan, or live infrastructure assessment. | [infrastructure.py](../backend/app/services/infrastructure.py) |
| Deployment risk | The score is a deterministic heuristic, not a calibrated probability or deployment approval. Missing inputs are explicit and produce `insufficient_data`. | [risk.py](../backend/app/services/risk.py), [schemas.py](../backend/app/schemas.py) |
| Notifications | Rules can be stored and listed in-app. They are not evaluated against events and no outbound webhook sender exists. URL checks are syntax-level only; do not enable delivery without DNS-pinned egress protections. | [notifications.py](../backend/app/services/notifications.py), [DG-INT-001](engineering-backlog/tasks.json) |
| Authentication | Optional single API key protects mutation routes; production configuration now requires a key. Read routes remain unauthenticated, so this is not RBAC or complete application authentication. | [config.py](../backend/app/config.py), [auth.py](../backend/app/auth.py), [README.md](../README.md) |
| Local runtime | Compose has localhost-bound ports, a named PostgreSQL volume, API readiness check, and build-time frontend API configuration. Local development credentials are not production secrets. | [docker-compose.yml](../docker-compose.yml), [frontend/Dockerfile](../frontend/Dockerfile) |

## Confirmed defects corrected

1. `DEPLOYGUARD_API_KEY` from `.env.example` was not mapped to the `api_key` setting. The setting
   now accepts the documented name (and `API_KEY` for compatibility), production mode rejects a
   missing key, and comparison uses `hmac.compare_digest`.
2. The API created tables during startup even though Compose already ran Alembic. Startup no
   longer silently creates schema; native startup now documents `alembic upgrade head` first.
3. Each pipeline run previously replaced the workflow's findings and the earlier run status.
   `pipeline_executions` now stores run history, optional source IDs are idempotent, and a paginated
   history endpoint is available. The static workflow findings remain intact.
4. An omitted risk payload previously looked like a zero-risk deployment. Missing evidence is now
   listed, the assessment is marked `insufficient_data`, and invalid custom weights return 422.
5. Flaky detection previously merged same-named tests across suites and counted skips in its
   denominator. It now groups by suite and test name and excludes skipped outcomes.
6. Terraform plan input previously ignored malformed nested structures and treated replacements as
   ordinary deletions. It now rejects malformed shapes and reports replacements, missing tags, and
   sensitive planned attributes without exposing sensitive values.
7. Webhook URL validation previously allowed non-loopback private IPs and plain HTTP. It now
   requires HTTPS and rejects credentials, reserved local names, and non-global literal addresses.
   The unsafe, unused outbound sender was removed; there is still no delivery path.
8. Compose previously passed `VITE_API_URL` at runtime, after Vite had already built static assets.
   It is now a build argument. PostgreSQL data is explicitly assigned a named volume.

The initial migration already existed. Its backlog description incorrectly claimed no revision or
migration configuration existed; that item was replaced with the remaining concern: detecting
partially created or drifted legacy schemas. The CI and migration-documentation backlog entries
were also narrowed to work not already present.

## Remaining priorities

### Before exposing the service to other users

- Replace the single optional API key with a complete authentication/authorization model, and protect
  read endpoints that expose pipeline and test history.
- Supply secrets through an appropriate secrets manager, rotate development defaults, and configure
  TLS termination and operational monitoring.
- If webhooks are implemented, resolve and pin DNS answers to public IPs, block private/reserved
  IPv4 and IPv6 destinations, validate every redirect, and add controlled-resolver tests first.

### Before treating analyses as deployment controls

- Use GitHub's documented workflow semantics and add trigger, matrix, dependency-cycle, and
  source-location validation.
- Replace regex Terraform parsing with a parser and clearly report unsupported constructs.
- Calibrate and document risk semantics; missing evidence must never imply approval.
- Automate PostgreSQL migration integration coverage in CI and add explicit UTC serialization tests
  for both database dialects. SQLite drops timezone metadata on retrieval.
- Bound test-history analytics queries and define retention for execution records.

## Verification and environment notes

Backend, frontend, Docker, and migration verification results are recorded in
[PROJECT_STATUS.md](PROJECT_STATUS.md). Host port 5432 was occupied, so the stack was started on
localhost port 5433. PostgreSQL and API health checks passed, Alembic reached head, the dashboard
returned HTTP 200, and execution-history/idempotency smoke checks passed. The smoke-test records were
removed afterward. At the user's request, the old anonymous volume was deleted after confirming no
container used it; the new named volume is active. The old database contents are therefore gone.
