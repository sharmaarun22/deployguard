from pydantic import BaseModel, Field


class PipelineAnalyzeRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    repository: str | None = Field(default=None, max_length=500)
    source: str = Field(min_length=1)


class PipelineExecutionRequest(BaseModel):
    pipeline_id: int
    status: str = Field(pattern="^(success|failure|cancelled|unknown)$")
    external_id: str | None = Field(default=None, min_length=1, max_length=200)
    log_text: str = Field(default="", max_length=500_000)


class TestReportRequest(BaseModel):
    report_format: str = Field(pattern="^(junit|robot)$")
    xml: str = Field(min_length=1, max_length=5_000_000)


class InfrastructureAnalyzeRequest(BaseModel):
    source_type: str = Field(pattern="^(terraform|plan)$")
    content: str = Field(min_length=1, max_length=5_000_000)


class DeploymentRiskRequest(BaseModel):
    pipeline_failures: int | None = Field(default=None, ge=0)
    failed_tests: int | None = Field(default=None, ge=0)
    flaky_tests: int | None = Field(default=None, ge=0)
    infrastructure_findings: int | None = Field(default=None, ge=0)
    missing_validation: bool | None = None
    previous_deployment_failures: int | None = Field(default=None, ge=0)
    weights: dict[str, float] | None = None


class Finding(BaseModel):
    rule: str
    severity: str
    message: str
    evidence: list[str] = Field(default_factory=list)


class NotificationRuleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    event_type: str = Field(min_length=1, max_length=100)
    minimum_severity: str = Field(pattern="^(low|medium|high|critical)$")
    webhook_url: str | None = Field(default=None, max_length=2000)
    enabled: bool = True
