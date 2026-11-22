import pytest

from backend.app.services.infrastructure import analyze_plan, analyze_terraform
from backend.app.services.risk import calculate_risk


def test_detects_insecure_s3_and_tags() -> None:
    terraform = """
resource "aws_s3_bucket" "public" {
  acl = "public-read"
}
"""
    findings = analyze_terraform(terraform)
    rules = {item["rule"] for item in findings}
    assert "public-s3-acl" in rules
    assert "missing-s3-encryption" in rules
    assert "missing-resource-tags" in rules


def test_rejects_malformed_plan() -> None:
    with pytest.raises(ValueError, match="Malformed Terraform plan"):
        analyze_plan("{")


def test_plan_reports_deletion() -> None:
    findings = analyze_plan(
        '{"resource_changes":[{"address":"aws_s3_bucket.old","change":{"actions":["delete"],"after":null}}]}'
    )
    assert findings[0]["rule"] == "plan-resource-deletion"


def test_plan_reports_replacement_missing_tags_and_sensitive_changes() -> None:
    findings = analyze_plan(
        """
        {"resource_changes":[{"address":"aws_instance.app","change":{
          "actions":["delete","create"],"after":{"tags":{}},
          "after_sensitive":{"password":true}
        }}]}
        """
    )
    assert {item["rule"] for item in findings} == {
        "plan-resource-replacement",
        "plan-missing-tags",
        "plan-sensitive-change",
    }


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ('{"resource_changes":{}}', "resource_changes must be an array"),
        (
            '{"resource_changes":[{"address":"aws_instance.app","change":{"actions":"delete"}}]}',
            "actions must be an array",
        ),
    ],
)
def test_rejects_malformed_plan_shapes(content: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        analyze_plan(content)


def test_risk_is_deterministic_and_bounded() -> None:
    first = calculate_risk({"pipeline_failures": 2, "failed_tests": 3, "missing_validation": True})
    second = calculate_risk({"pipeline_failures": 2, "failed_tests": 3, "missing_validation": True})
    assert first == second
    assert first["score"] <= 100


def test_risk_distinguishes_missing_evidence_from_measured_zero() -> None:
    incomplete = calculate_risk({})
    complete = calculate_risk(
        {
            "pipeline_failures": 0,
            "failed_tests": 0,
            "flaky_tests": 0,
            "infrastructure_findings": 0,
            "missing_validation": False,
            "previous_deployment_failures": 0,
        }
    )
    assert incomplete["classification"] == "insufficient_data"
    assert incomplete["missing_data"]
    assert complete["classification"] == "low"
    assert complete["missing_data"] == []


def test_rejects_invalid_risk_weights() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        calculate_risk({"pipeline_failures": 1}, {"pipeline_failures": -1})
