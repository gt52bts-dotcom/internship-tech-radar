"""Deterministic AWS service mention detection for S1 public sources.

S1 passes only text fetched during the current run into this module. The rules
identify service *mentions*; they deliberately do not claim that two services
form a validated architecture or that either service is recommended.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re


# These are canonical AWS service names and their common names on AWS pages.
# They are detection rules, not a fabricated service catalogue or evidence.
SERVICE_ALIASES = {
    "api gateway": "API Gateway",
    "aws devops agent": "AWS DevOps Agent",
    "cloudformation": "CloudFormation",
    "cloudfront": "CloudFront",
    "cloudwatch synthetics": "CloudWatch Synthetics",
    "cloudwatch": "CloudWatch",
    "dynamodb": "DynamoDB",
    "ec2": "EC2",
    "efs": "EFS",
    "eventbridge": "EventBridge",
    "lambda": "Lambda",
    "s3 files": "S3 Files",
    "amazon s3": "S3",
    "s3": "S3",
    "step functions": "Step Functions",
    "vpc": "VPC",
}

TAG_PATTERNS = {
    "storage": ("storage", "s3", "file system", "file sharing"),
    "serverless": ("lambda", "api gateway", "eventbridge"),
    "networking": ("vpc", "cloudfront", "network"),
    "operations": ("cloudwatch", "synthetics", "monitoring"),
    "ci_cd": ("ci/cd", "ci cd", "continuous integration", "continuous deployment", "github actions", "pipeline"),
    "developer_tools": ("developer tooling", "developer platform", "github actions", "devops"),
    "infrastructure": ("cloudformation", "step functions", "infrastructure as code"),
}


@dataclass
class ServiceMention:
    """One service name found in text retrieved during the current S1 run."""

    name: str
    aliases: set[str] = field(default_factory=set)
    first_mention_position: int = 1_000_000_000

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "matched_terms": sorted(self.aliases),
            "first_mention_position": self.first_mention_position,
            "evidence_basis": "fetched_source_text_rule_match",
        }


def detect_service_signals(text: str) -> dict[str, object]:
    """Find AWS service names in real page text with deterministic rules."""

    mentions: dict[str, ServiceMention] = {}
    for alias, canonical_name in SERVICE_ALIASES.items():
        position = _alias_position(text, alias)
        if position is None:
            continue

        mention = mentions.setdefault(canonical_name, ServiceMention(canonical_name))
        mention.aliases.add(alias)
        mention.first_mention_position = min(mention.first_mention_position, position)

    detected = [mention.to_dict() for mention in mentions.values()]
    detected.sort(key=lambda item: (item["first_mention_position"], -len(str(item["name"])), str(item["name"])))
    return {
        "strategy": "deterministic_rules_on_fetched_public_source_text",
        "detected_services": detected,
        "limits": [
            "A detected name is a text mention, not a validated dependency graph.",
            "S1 does not use LLM hints, manually supplied metadata, or static case-study data.",
        ],
    }


def service_names(service_detection: dict[str, object]) -> list[str]:
    """Return service names in the order they first appear in the page."""

    return [str(item["name"]) for item in service_detection.get("detected_services", [])]


def tags_from_text(text: str) -> list[str]:
    """Attach broad routing tags for later stages without making a recommendation."""

    lowered = text.lower()
    return [tag for tag, patterns in TAG_PATTERNS.items() if any(pattern in lowered for pattern in patterns)]


def _alias_position(text: str, alias: str) -> int | None:
    match = re.search(rf"\b{re.escape(alias)}\b", text, re.IGNORECASE)
    return match.start() if match else None
