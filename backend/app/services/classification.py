import re

RULES = [
    (
        "dependency-install",
        "Dependency installation failure",
        [r"npm ci", r"pip install", r"could not resolve", r"not found"],
    ),
    (
        "authentication",
        "Authentication failure",
        [r"unauthorized", r"authentication", r"forbidden", r"invalid credential"],
    ),
    (
        "network",
        "Network failure",
        [r"timeout", r"dns", r"connection refused", r"network is unreachable"],
    ),
    (
        "resource-exhaustion",
        "Resource exhaustion",
        [r"no space left", r"out of memory", r"oom", r"too many open files"],
    ),
    (
        "test-assertion",
        "Test assertion failure",
        [r"assert", r"assertionerror", r"pytest", r"expected"],
    ),
    (
        "configuration",
        "Configuration error",
        [r"configuration", r"missing.*environment", r"invalid.*yaml", r"syntax error"],
    ),
    ("build", "Build failure", [r"compile error", r"build failed", r"tsc", r"gcc"]),
]


def classify_failure(log_text: str) -> dict[str, object]:
    normalized = log_text.lower()
    matches: list[tuple[str, str, list[str]]] = []
    for category, label, patterns in RULES:
        evidence = [pattern for pattern in patterns if re.search(pattern, normalized)]
        if evidence:
            matches.append((category, label, evidence))

    if not matches:
        return {
            "category": "unknown",
            "confidence": 0.0,
            "evidence": [],
            "investigation": [
                "Review the complete pipeline log",
                "Compare the failure with a known-good run",
            ],
        }

    category, label, evidence = matches[0]
    confidence = min(0.95, 0.45 + 0.15 * len(evidence))
    return {
        "category": category,
        "label": label,
        "confidence": confidence,
        "evidence": evidence,
        "investigation": [
            "Inspect the matching error lines",
            "Re-run the failed step in isolation",
        ],
    }
