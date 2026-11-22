import json
import logging
from typing import Annotated
from xml.etree import ElementTree

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.app.auth import require_api_key
from backend.app.db import Base, engine, get_db
from backend.app.models import (
    InfrastructureFinding,
    Notification,
    NotificationRule,
    Pipeline,
    TestExecution,
)
from backend.app.schemas import (
    DeploymentRiskRequest,
    InfrastructureAnalyzeRequest,
    NotificationRuleRequest,
    PipelineAnalyzeRequest,
    PipelineExecutionRequest,
    TestReportRequest,
)
from backend.app.services.classification import classify_failure
from backend.app.services.infrastructure import analyze_plan, analyze_terraform
from backend.app.services.notifications import validate_webhook_url
from backend.app.services.pipeline import analyze_workflow
from backend.app.services.risk import calculate_risk
from backend.app.services.test_intelligence import flaky_scores, parse_junit_xml, parse_robot_xml

logging.basicConfig(level="INFO")
logger = logging.getLogger("deployguard")

app = FastAPI(title="DeployGuard", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready")
def health_ready(db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.post("/api/pipelines/analyze")
def analyze_pipeline(
    payload: PipelineAnalyzeRequest,
    db: Annotated[Session, Depends(get_db)],
    _authorized: Annotated[None, Depends(require_api_key)],
) -> dict[str, object]:
    try:
        result = analyze_workflow(payload.source)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    pipeline = Pipeline(
        name=payload.name,
        repository=payload.repository,
        status="unknown",
        source=payload.source,
        findings=json.dumps(result["findings"]),
    )
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return {"id": pipeline.id, **result}


@app.post("/api/pipelines/executions")
def record_execution(
    payload: PipelineExecutionRequest,
    db: Annotated[Session, Depends(get_db)],
    _authorized: Annotated[None, Depends(require_api_key)],
) -> dict[str, object]:
    pipeline = db.get(Pipeline, payload.pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline.status = payload.status
    classification = (
        classify_failure(payload.log_text)
        if payload.status == "failure"
        else {
            "category": "none",
            "confidence": 1.0,
            "evidence": [],
            "investigation": [],
        }
    )
    pipeline.findings = json.dumps([classification])
    db.commit()
    db.refresh(pipeline)
    return {"pipeline_id": pipeline.id, "status": pipeline.status, "classification": classification}


@app.get("/api/pipelines")
def list_pipelines(
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict[str, object]:
    total = db.query(func.count(Pipeline.id)).scalar() or 0
    pipelines = db.query(Pipeline).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "repository": item.repository,
                "status": item.status,
                "findings": json.loads(item.findings),
            }
            for item in pipelines
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@app.post("/api/tests/reports")
def ingest_test_report(
    payload: TestReportRequest,
    db: Annotated[Session, Depends(get_db)],
    _authorized: Annotated[None, Depends(require_api_key)],
) -> dict[str, object]:
    try:
        records = (
            parse_junit_xml(payload.xml)
            if payload.report_format == "junit"
            else parse_robot_xml(payload.xml)
        )
    except (ElementTree.ParseError, ValueError) as exc:
        raise HTTPException(
            status_code=422, detail=f"Invalid {payload.report_format.upper()} report: {exc}"
        ) from exc

    executions = [
        TestExecution(
            report_format=payload.report_format,
            suite=str(record["suite"]),
            test_name=str(record["test_name"]),
            status=str(record["status"]),
            duration_ms=float(record["duration_ms"]),
            failure_message=str(record["failure_message"])
            if record["failure_message"] is not None
            else None,
        )
        for record in records
    ]
    db.add_all(executions)
    db.commit()
    return {"format": payload.report_format, "tests_ingested": len(executions)}


@app.get("/api/tests")
def test_analytics(
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    records = db.query(TestExecution).all()
    serializable = [
        {"test_name": item.test_name, "status": item.status, "duration_ms": item.duration_ms}
        for item in records
    ]
    flaky = flaky_scores(serializable)
    slow = [
        {"test_name": item.test_name, "status": item.status, "duration_ms": item.duration_ms}
        for item in sorted(records, key=lambda item: item.duration_ms, reverse=True)[:20]
    ]
    return {
        "total_executions": len(records),
        "flaky_tests": flaky,
        "slow_tests": slow,
    }


@app.post("/api/infrastructure/analyze")
def analyze_infrastructure(
    payload: InfrastructureAnalyzeRequest,
    db: Annotated[Session, Depends(get_db)],
    _authorized: Annotated[None, Depends(require_api_key)],
) -> dict[str, object]:
    try:
        findings = (
            analyze_terraform(payload.content)
            if payload.source_type == "terraform"
            else analyze_plan(payload.content)
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    for finding in findings:
        db.add(
            InfrastructureFinding(
                source_type=payload.source_type,
                resource="terraform",
                rule=finding["rule"],
                severity=finding["severity"],
                description=finding["description"],
            )
        )
    db.commit()
    return {
        "source_type": payload.source_type,
        "analysis_scope": "static local configuration",
        "findings": findings,
    }


@app.post("/api/deployments/risk")
def deployment_risk(payload: DeploymentRiskRequest) -> dict[str, object]:
    values = payload.model_dump(exclude={"weights"})
    return calculate_risk(values, payload.weights)


@app.post("/api/notifications/rules")
def create_notification_rule(
    payload: NotificationRuleRequest,
    db: Annotated[Session, Depends(get_db)],
    _authorized: Annotated[None, Depends(require_api_key)],
) -> dict[str, object]:
    if payload.webhook_url:
        try:
            validate_webhook_url(payload.webhook_url)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    rule = NotificationRule(
        name=payload.name,
        event_type=payload.event_type,
        minimum_severity=payload.minimum_severity,
        webhook_url=payload.webhook_url,
        enabled=payload.enabled,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {"id": rule.id, "name": rule.name, "enabled": rule.enabled}


@app.get("/api/notifications")
def list_notifications(
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict[str, object]:
    total = db.query(func.count(Notification.id)).scalar() or 0
    items = (
        db.query(Notification)
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [
            {
                "id": item.id,
                "event_type": item.event_type,
                "severity": item.severity,
                "title": item.title,
                "message": item.message,
                "acknowledged": item.acknowledged,
            }
            for item in items
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@app.get("/api/dashboard")
def dashboard(
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    pipelines = db.query(Pipeline).all()
    tests = db.query(TestExecution).all()
    findings = db.query(InfrastructureFinding).all()
    failed_pipelines = sum(item.status == "failure" for item in pipelines)
    failed_tests = sum(item.status == "failed" for item in tests)
    test_records = [
        {"test_name": item.test_name, "status": item.status, "duration_ms": item.duration_ms}
        for item in tests
    ]
    return {
        "pipeline_health": {
            "total": len(pipelines),
            "failed": failed_pipelines,
            "successful": sum(item.status == "success" for item in pipelines),
        },
        "test_reliability": {
            "total_executions": len(tests),
            "failed_executions": failed_tests,
            "flaky_tests": flaky_scores(test_records),
        },
        "infrastructure_findings": len(findings),
        "recent_pipelines": [
            {"id": item.id, "name": item.name, "status": item.status} for item in pipelines[-10:]
        ],
    }
