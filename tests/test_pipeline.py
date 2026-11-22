import pytest

from backend.app.services.classification import classify_failure
from backend.app.services.pipeline import analyze_workflow


def test_analyzes_valid_workflow() -> None:
    source = """
name: CI
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
"""
    result = analyze_workflow(source)
    assert result["valid"] is True
    assert result["job_count"] == 1


def test_rejects_missing_jobs() -> None:
    with pytest.raises(ValueError, match="at least one job"):
        analyze_workflow("name: CI")


def test_rejects_malformed_yaml() -> None:
    with pytest.raises(ValueError, match="Malformed YAML"):
        analyze_workflow("jobs: [")


def test_reports_missing_dependency() -> None:
    source = """
jobs:
  deploy:
    needs: missing
    runs-on: ubuntu-latest
"""
    result = analyze_workflow(source)
    assert any(item["rule"] == "missing-job-dependency" for item in result["findings"])


def test_failure_classifier_is_uncertain_when_unknown() -> None:
    result = classify_failure("process terminated")
    assert result["category"] == "unknown"
    assert result["confidence"] == 0.0


def test_dependency_failure_classifier() -> None:
    result = classify_failure("pip install failed: could not resolve package")
    assert result["category"] == "dependency-install"
