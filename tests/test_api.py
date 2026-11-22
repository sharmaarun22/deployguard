from fastapi.testclient import TestClient

WORKFLOW = """
name: CI
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
"""

JUNIT = """
<testsuite name="api-tests">
  <testcase classname="api" name="test_health" time="0.1"/>
  <testcase classname="api" name="test_login" time="0.2">
    <failure message="assertion failed"/>
  </testcase>
</testsuite>
"""


def test_health_and_database_readiness(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/health/ready").json() == {"status": "ready"}


def test_pipeline_analysis_execution_and_pagination(client: TestClient) -> None:
    analyzed = client.post(
        "/api/pipelines/analyze",
        json={"name": "ci", "repository": "example/project", "source": WORKFLOW},
    )
    assert analyzed.status_code == 200
    pipeline_id = analyzed.json()["id"]

    execution = client.post(
        "/api/pipelines/executions",
        json={
            "pipeline_id": pipeline_id,
            "status": "failure",
            "external_id": "run-1",
            "log_text": "AssertionError: expected success",
        },
    )
    assert execution.status_code == 200
    assert execution.json()["classification"]["category"] == "test-assertion"
    assert execution.json()["duplicate"] is False

    duplicate = client.post(
        "/api/pipelines/executions",
        json={
            "pipeline_id": pipeline_id,
            "status": "success",
            "external_id": "run-1",
        },
    )
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["execution_id"] == execution.json()["execution_id"]

    next_execution = client.post(
        "/api/pipelines/executions",
        json={"pipeline_id": pipeline_id, "status": "success", "external_id": "run-2"},
    )
    assert next_execution.status_code == 200
    history = client.get(f"/api/pipelines/{pipeline_id}/executions")
    assert history.json()["total"] == 2

    listing = client.get("/api/pipelines?page=1&page_size=1")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["id"] == pipeline_id
    assert listing.json()["items"][0]["status"] == "success"


def test_invalid_pipeline_and_unknown_execution_errors(client: TestClient) -> None:
    invalid = client.post(
        "/api/pipelines/analyze",
        json={"name": "invalid", "source": "jobs: ["},
    )
    assert invalid.status_code == 422

    missing = client.post(
        "/api/pipelines/executions",
        json={"pipeline_id": 404, "status": "failure"},
    )
    assert missing.status_code == 404


def test_execution_preserves_workflow_findings(client: TestClient) -> None:
    source = """
name: CI
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: curl https://example.com/script.sh | bash
"""
    analyzed = client.post(
        "/api/pipelines/analyze",
        json={"name": "unsafe-workflow", "source": source},
    )
    assert any(item["rule"] == "unsafe-shell-pipe" for item in analyzed.json()["findings"])

    client.post(
        "/api/pipelines/executions",
        json={"pipeline_id": analyzed.json()["id"], "status": "failure"},
    )
    stored = client.get("/api/pipelines").json()["items"][0]
    assert any(item["rule"] == "unsafe-shell-pipe" for item in stored["findings"])


def test_junit_ingestion_updates_analytics_and_dashboard(client: TestClient) -> None:
    result = client.post(
        "/api/tests/reports",
        json={"report_format": "junit", "xml": JUNIT},
    )
    assert result.status_code == 200
    assert result.json()["tests_ingested"] == 2
    analytics = client.get("/api/tests").json()
    assert analytics["total_executions"] == 2
    assert len(analytics["slow_tests"]) == 2
    assert client.get("/api/dashboard").json()["test_reliability"]["failed_executions"] == 1


def test_static_infrastructure_analysis_and_risk(client: TestClient) -> None:
    terraform = """
resource "aws_s3_bucket" "public" {
  acl = "public-read"
}
"""
    response = client.post(
        "/api/infrastructure/analyze",
        json={"source_type": "terraform", "content": terraform},
    )
    assert response.status_code == 200
    assert response.json()["analysis_scope"] == "static local configuration"
    assert any(item["rule"] == "public-s3-acl" for item in response.json()["findings"])

    risk = client.post("/api/deployments/risk", json={"pipeline_failures": 1})
    assert risk.status_code == 200
    assert risk.json()["score"] > 0
    assert risk.json()["classification"] == "insufficient_data"

    invalid_weights = client.post(
        "/api/deployments/risk",
        json={"pipeline_failures": 1, "weights": {"pipeline_failures": -1}},
    )
    assert invalid_weights.status_code == 422


def test_api_key_protects_notification_rule_mutations(client: TestClient, monkeypatch) -> None:
    from backend.app.config import settings

    monkeypatch.setattr(settings, "api_key", "test-secret")
    rule = {
        "name": "Critical failures",
        "event_type": "pipeline.failed",
        "minimum_severity": "critical",
        "enabled": True,
    }
    assert client.post("/api/notifications/rules", json=rule).status_code == 401

    headers = {"X-API-Key": "test-secret"}
    unsafe = {**rule, "webhook_url": "http://127.0.0.1/hook"}
    assert client.post("/api/notifications/rules", json=unsafe, headers=headers).status_code == 422

    created = client.post(
        "/api/notifications/rules",
        json={**rule, "webhook_url": "https://hooks.example.com/deployguard"},
        headers=headers,
    )
    assert created.status_code == 200
    assert created.json()["enabled"] is True
    assert client.get("/api/notifications").json()["total"] == 0
