from typing import Any

import yaml


def analyze_workflow(source: str) -> dict[str, Any]:
    try:
        document = yaml.safe_load(source)
    except yaml.YAMLError as exc:
        raise ValueError(f"Malformed YAML: {exc}") from exc

    if not isinstance(document, dict):
        raise ValueError("Workflow must contain a YAML mapping")

    jobs = document.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        raise ValueError("Workflow must define at least one job")

    findings: list[dict[str, Any]] = []
    job_names = set(jobs)
    for name, job in jobs.items():
        if not isinstance(job, dict):
            findings.append(
                {
                    "rule": "invalid-job",
                    "severity": "high",
                    "message": f"Job '{name}' must be a mapping",
                }
            )
            continue

        needs = job.get("needs", [])
        if isinstance(needs, str):
            needs = [needs]
        if isinstance(needs, list):
            for dependency in needs:
                if dependency not in job_names:
                    findings.append(
                        {
                            "rule": "missing-job-dependency",
                            "severity": "high",
                            "message": f"Job '{name}' depends on missing job '{dependency}'",
                        }
                    )

        if "runs-on" not in job and "uses" not in job:
            findings.append(
                {
                    "rule": "missing-runs-on",
                    "severity": "medium",
                    "message": f"Job '{name}' has neither 'runs-on' nor reusable 'uses'",
                }
            )

        steps = job.get("steps")
        if isinstance(steps, list):
            for index, step in enumerate(steps):
                if isinstance(step, dict) and "run" in step:
                    command = str(step["run"]).lower()
                    if "curl " in command and "| bash" in command:
                        findings.append(
                            {
                                "rule": "unsafe-shell-pipe",
                                "severity": "high",
                                "message": (
                                    f"Job '{name}' step {index + 1} pipes "
                                    "remote content into bash"
                                ),
                            }
                        )

    return {
        "valid": not any(item["severity"] == "high" for item in findings),
        "job_count": len(jobs),
        "job_names": sorted(job_names),
        "findings": findings,
    }
