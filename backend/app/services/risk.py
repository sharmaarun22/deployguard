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
    applied = {**DEFAULT_WEIGHTS, **(weights or {})}
    factors: list[dict[str, Any]] = []
    score = 0.0

    for key, weight in applied.items():
        value = values.get(key, False)
        if isinstance(value, bool):
            contribution = weight if value else 0.0
        else:
            contribution = float(value) * weight
        if contribution:
            score += contribution
            factors.append(
                {"factor": key, "value": value, "weight": weight, "score": round(contribution, 2)}
            )

    score = min(100.0, round(score, 2))
    classification = (
        "low" if score < 25 else "medium" if score < 50 else "high" if score < 75 else "critical"
    )
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
        "factors": factors,
        "recommended_actions": actions,
    }
