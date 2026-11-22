import math
from typing import Any

DEFAULT_WEIGHTS = {
    "pipeline_failures": 15.0,
    "failed_tests": 10.0,
    "flaky_tests": 5.0,
    "infrastructure_findings": 8.0,
    "missing_validation": 20.0,
    "previous_deployment_failures": 12.0,
}


def calculate_risk(
    values: dict[str, Any], weights: dict[str, float] | None = None
) -> dict[str, Any]:
    overrides = weights or {}
    unknown_weights = set(overrides) - set(DEFAULT_WEIGHTS)
    if unknown_weights:
        raise ValueError(f"Unknown risk weight(s): {', '.join(sorted(unknown_weights))}")
    for key, weight in overrides.items():
        if not math.isfinite(weight) or weight < 0:
            raise ValueError(f"Risk weight '{key}' must be finite and non-negative")

    applied = {**DEFAULT_WEIGHTS, **(weights or {})}
    factors: list[dict[str, Any]] = []
    score = 0.0
    missing_data: list[str] = []

    for key, weight in applied.items():
        value = values.get(key)
        if value is None:
            missing_data.append(key)
            continue
        if isinstance(value, bool):
            contribution = weight if value else 0.0
        else:
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"Risk input '{key}' must be finite and non-negative")
            contribution = float(value) * weight
        score += contribution
        factors.append(
            {"factor": key, "value": value, "weight": weight, "score": round(contribution, 2)}
        )

    score = min(100.0, round(score, 2))
    risk_level = (
        "low" if score < 25 else "medium" if score < 50 else "high" if score < 75 else "critical"
    )
    classification = "insufficient_data" if missing_data else risk_level
    actions: list[str] = []
    if values.get("pipeline_failures", 0):
        actions.append("Investigate and resolve recent pipeline failures")
    if values.get("flaky_tests", 0):
        actions.append("Review flaky tests before approving the release")
    if values.get("infrastructure_findings", 0):
        actions.append("Review infrastructure findings and intended resource changes")
    if values.get("missing_validation"):
        actions.append("Add required pre-deployment validation")

    return {
        "score": score,
        "classification": classification,
        "risk_level": risk_level,
        "data_completeness": "complete" if not missing_data else "incomplete",
        "missing_data": missing_data,
        "factors": factors,
        "recommended_actions": actions,
    }
