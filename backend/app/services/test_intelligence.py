from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import TypedDict
from xml.etree import ElementTree


class ParsedTestRecord(TypedDict):
    suite: str
    test_name: str
    status: str
    duration_ms: float
    failure_message: str | None


def _duration_ms(value: str | None) -> float:
    try:
        duration_ms = float(value or 0) * 1000
    except ValueError as exc:
        raise ValueError("Test duration must be numeric") from exc
    if not math.isfinite(duration_ms) or duration_ms < 0:
        raise ValueError("Test duration must be finite and non-negative")
    return duration_ms


def parse_junit_xml(xml_text: str) -> list[ParsedTestRecord]:
    root = ElementTree.fromstring(xml_text)
    records: list[ParsedTestRecord] = []
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
                "duration_ms": _duration_ms(case.get("time")),
                "failure_message": message,
            }
        )
    if not records:
        raise ValueError("JUnit XML contains no testcase elements")
    return records


def parse_robot_xml(xml_text: str) -> list[ParsedTestRecord]:
    root = ElementTree.fromstring(xml_text)
    records: list[ParsedTestRecord] = []
    for test in root.iter("test"):
        name = test.get("name") or "unknown"
        status_node = test.find(".//status")
        status_text = "FAIL"
        if status_node is not None:
            status_text = status_node.get("status") or status_node.text or "FAIL"
        status_text = status_text.upper()
        status = "passed" if status_text == "PASS" else "failed"
        duration_ms = (
            _duration_ms(status_node.get("elapsed"))
            if status_node is not None
            else 0.0
        )
        message_node = test.find(".//status/msg")
        records.append(
            {
                "suite": "robot",
                "test_name": name,
                "status": status,
                "duration_ms": duration_ms,
                "failure_message": message_node.text if message_node is not None else None,
            }
        )
    if not records:
        raise ValueError("Robot XML contains no test elements")
    return records


def flaky_scores(
    records: Sequence[Mapping[str, object]], minimum_runs: int = 3
) -> list[dict[str, object]]:
    if minimum_runs < 2:
        raise ValueError("minimum_runs must be at least 2")
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for record in records:
        status = str(record["status"])
        if status not in {"passed", "failed"}:
            continue
        groups[(str(record.get("suite", "unknown")), str(record["test_name"]))].append(status)
    scores: list[dict[str, object]] = []
    for (suite, name), statuses in groups.items():
        runs = len(statuses)
        if runs < minimum_runs:
            continue
        passed = statuses.count("passed")
        failed = statuses.count("failed")
        if passed and failed:
            scores.append(
                {
                    "suite": suite,
                    "test_name": name,
                    "runs": runs,
                    "passed": passed,
                    "failed": failed,
                    "pass_rate": round(passed / runs, 3),
                    "failure_rate": round(failed / runs, 3),
                    "flaky": True,
                    "score": round(failed * passed / (runs * runs), 3),
                }
            )
    return scores
