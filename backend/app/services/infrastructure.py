import json
import re
from collections.abc import Mapping


def _finding(
    rule: str,
    severity: str,
    resource: str,
    description: str,
    evidence: list[str],
    remediation: str,
) -> dict[str, object]:
    return {
        "rule": rule,
        "severity": severity,
        "resource": resource,
        "description": description,
        "evidence": evidence,
        "remediation": remediation,
    }


def analyze_terraform(content: str) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    resource_blocks = re.findall(
        r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{(.*?)\n\}', content, re.DOTALL
    )
    for resource_type, resource_name, body in resource_blocks:
        resource = f"{resource_type}.{resource_name}"
        if resource_type == "aws_s3_bucket":
            if re.search(r'acl\s*=\s*"public-read"', body):
                findings.append(
                    _finding(
                        "public-s3-acl",
                        "critical",
                        resource,
                        f"{resource} may be publicly readable",
                        ['acl = "public-read"'],
                        "Remove the public ACL and use an explicit bucket access policy.",
                    )
                )
            if "server_side_encryption_configuration" not in body:
                findings.append(
                    _finding(
                        "missing-s3-encryption",
                        "high",
                        resource,
                        f"{resource} does not declare server-side encryption",
                        ["server_side_encryption_configuration is absent"],
                        "Enable an approved server-side encryption configuration.",
                    )
                )
        if resource_type == "aws_security_group" and re.search(
            r'(?:cidr_blocks\s*=\s*\[[^\]]*"0\.0\.0\.0/0"|ipv6_cidr_blocks\s*=\s*\[[^\]]*"::/0")',
            body,
        ):
            findings.append(
                _finding(
                    "open-security-group",
                    "high",
                    resource,
                    f"{resource} allows ingress from the public internet",
                    ["Ingress includes 0.0.0.0/0 or ::/0"],
                    "Restrict ingress to the smallest required trusted CIDR ranges.",
                )
            )
        if not re.search(r"\btags\s*=", body):
            findings.append(
                _finding(
                    "missing-resource-tags",
                    "medium",
                    resource,
                    f"{resource} does not declare resource tags",
                    ["No tags assignment was found in the resource block"],
                    "Add the organization-required ownership, environment, and cost tags.",
                )
            )
    return findings


def _contains_sensitive_value(value: object) -> bool:
    if value is True:
        return True
    if isinstance(value, Mapping):
        return any(_contains_sensitive_value(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_sensitive_value(item) for item in value)
    return False


def analyze_plan(content: str) -> list[dict[str, object]]:
    try:
        plan = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed Terraform plan JSON: {exc}") from exc
    if not isinstance(plan, dict):
        raise ValueError("Terraform plan must be a JSON object")

    changes = plan.get("resource_changes", [])
    if not isinstance(changes, list):
        raise ValueError("Terraform plan resource_changes must be an array")

    findings: list[dict[str, object]] = []
    for index, item in enumerate(changes):
        if not isinstance(item, dict):
            raise ValueError(f"Terraform resource change {index} must be an object")
        address = str(item.get("address", "unknown"))
        change = item.get("change", {})
        if not isinstance(change, dict):
            raise ValueError(f"Terraform resource change '{address}' must contain a change object")
        actions = change.get("actions", [])
        if not isinstance(actions, list) or not all(isinstance(action, str) for action in actions):
            raise ValueError(
                f"Terraform resource change '{address}' actions must be an array of strings"
            )

        deletes = "delete" in actions
        creates = "create" in actions
        if deletes:
            is_replacement = creates
            findings.append(
                _finding(
                    "plan-resource-replacement" if is_replacement else "plan-resource-deletion",
                    "critical" if is_replacement else "high",
                    address,
                    (
                        f"{address} is scheduled for replacement"
                        if is_replacement
                        else f"{address} is scheduled for deletion"
                    ),
                    [f"Planned actions: {', '.join(actions)}"],
                    (
                        "Review the replacement impact, data retention, and dependent resources."
                        if is_replacement
                        else "Confirm deletion is intended and that required data is backed up."
                    ),
                )
            )

        after = change.get("after")
        if isinstance(after, dict) and any(action in {"create", "update"} for action in actions):
            tags = after.get("tags")
            if not isinstance(tags, dict) or not tags:
                findings.append(
                    _finding(
                        "plan-missing-tags",
                        "medium",
                        address,
                        f"{address} has no tags in the planned state",
                        ["Planned tags are absent or empty"],
                        "Add the organization-required ownership, environment, and cost tags.",
                    )
                )

        if _contains_sensitive_value(change.get("after_sensitive")):
            findings.append(
                _finding(
                    "plan-sensitive-change",
                    "medium",
                    address,
                    f"{address} contains sensitive planned attributes",
                    ["Terraform marks one or more planned attributes as sensitive"],
                    "Review sensitive changes securely; do not expose plan values in logs.",
                )
            )
    return findings
