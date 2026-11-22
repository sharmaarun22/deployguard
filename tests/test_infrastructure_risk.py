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


def test_risk_is_deterministic_and_bounded() -> None:
    first = calculate_risk({"pipeline_failures": 2, "failed_tests": 3, "missing_validation": True})
    second = calculate_risk({"pipeline_failures": 2, "failed_tests": 3, "missing_validation": True})
    assert first == second
    assert first["score"] <= 100
