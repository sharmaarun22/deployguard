from __future__ import annotations

from collections import defaultdict
from xml.etree import ElementTree


def parse_junit_xml(xml_text: str) -> list[dict[str, object]]:
    root = ElementTree.fromstring(xml_text)
    records: list[dict[str, object]] = []
    for case in root.iter("testcase"):
        failure = case.find("failure")
        error = case.find("error")
        skipped = case.find("skipped")
        if failure is not None or error is not None:
            status = "failed"
        elif skipped is not None:
            status = "skipped"
        else:
            status = "passed"
        node = failure if failure is not None else error
        message = node.get("message") if node is not None else None
        records.append(
            {
                "suite": case.get("classname") or (root.get("name") or "unknown"),
                "test_name": case.get("name") or "unknown",
                "status": status,
                "duration_ms": float(case.get("time", "0") or 0) * 1000,
                "failure_message": message,
            }
        )
    if not records:
        raise ValueError("JUnit XML contains no testcase elements")
    return records


def parse_robot_xml(xml_text: str) -> list[dict[str, object]]:
    root = ElementTree.fromstring(xml_text)
    records: list[dict[str, object]] = []
    for test in root.iter("test"):
        name = test.get("name") or "unknown"
        status_node = test.find(".//status")
        status_text = (
            status_node.get("status")
            if status_node is not None and status_node.get("status")
            else (status_node.text if status_node is not None and status_node.text else "FAIL")
        ).upper()
        status = "passed" if status_text == "PASS" else "failed"
        elapsed = float(status_node.get("elapsed", "0") or 0) if status_node is not None else 0
        message_node = test.find(".//status/msg")
        records.append(
            {
                "suite": "robot",
                "test_name": name,
                "status": status,
                "duration_ms": elapsed * 1000,
                "failure_message": message_node.text if message_node is not None else None,
            }
        )
    if not records:
        raise ValueError("Robot XML contains no test elements")
    return records


def flaky_scores(
    records: list[dict[str, object]], minimum_runs: int = 3
) -> list[dict[str, object]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for record in records:
        groups[str(record["test_name"])].append(str(record["status"]))
    scores: list[dict[str, object]] = []
    for name, statuses in groups.items():
        runs = len(statuses)
        if runs < minimum_runs:
            continue
        passed = statuses.count("passed")
        failed = statuses.count("failed")
        if passed and failed:
            scores.append(
                {
                    "test_name": name,
                    "runs": runs,
                    "pass_rate": round(passed / runs, 3),
                    "flaky": True,
                    "score": round(failed * passed / (runs * runs), 3),
                }
            )
    return scores
