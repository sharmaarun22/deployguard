import json
import re


def analyze_terraform(content: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    resource_blocks = re.findall(
        r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{(.*?)\n\}', content, re.DOTALL
    )
    for resource_type, resource_name, body in resource_blocks:
        resource = f"{resource_type}.{resource_name}"
        if resource_type == "aws_s3_bucket":
            if "acl" in body and re.search(r'acl\s*=\s*"public-read"', body):
                findings.append(
                    {
                        "rule": "public-s3-acl",
                        "severity": "critical",
                        "description": f"{resource} may be publicly readable",
                    }
                )
            if "server_side_encryption_configuration" not in body:
                findings.append(
                    {
                        "rule": "missing-s3-encryption",
                        "severity": "high",
                        "description": f"{resource} does not declare server-side encryption",
                    }
                )
        if resource_type == "aws_security_group":
            if re.search(r'cidr_blocks\s*=\s*\[[^\]]*"0\.0\.0\.0/0"', body):
                findings.append(
                    {
                        "rule": "open-security-group",
                        "severity": "high",
                        "description": f"{resource} allows ingress from 0.0.0.0/0",
                    }
                )
        if "tags" not in body:
            findings.append(
                {
                    "rule": "missing-resource-tags",
                    "severity": "medium",
                    "description": f"{resource} does not declare resource tags",
                }
            )
    return findings


def analyze_plan(content: str) -> list[dict[str, str]]:
    try:
        plan = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed Terraform plan JSON: {exc}") from exc
    if not isinstance(plan, dict):
        raise ValueError("Terraform plan must be a JSON object")

    findings: list[dict[str, str]] = []
    for change in plan.get("resource_changes", []):
        if not isinstance(change, dict):
            continue
        address = str(change.get("address", "unknown"))
        actions = change.get("change", {}).get("actions", [])
        if "delete" in actions:
            findings.append(
                {
                    "rule": "plan-resource-deletion",
                    "severity": "high",
                    "description": f"{address} is scheduled for deletion",
                }
            )
        after = change.get("change", {}).get("after")
        if isinstance(after, dict) and "tags" not in after:
            findings.append(
                {
                    "rule": "plan-missing-tags",
                    "severity": "medium",
                    "description": f"{address} has no tags in the planned state",
                }
            )
    return findings
