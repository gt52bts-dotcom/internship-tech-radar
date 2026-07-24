"""S0 demand-card normalization and validation.

S0 intentionally does not fetch URLs or search the web. It prepares and checks
the human problem statement before S1 is allowed to gather external evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import re
from typing import Any


ALLOWED_SOURCE_MODES = {"rss", "url", "paste", "service"}
DEFAULT_REGION = "ap-southeast-1"
DEFAULT_EXCLUDED_SERVICES = ["Bedrock"]
DEFAULT_MAX_SMALL_POC_USD = 3


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class AssistantFinding:
    code: str
    message: str
    question: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "message": self.message,
            "question": self.question,
        }


@dataclass
class DemandCardResult:
    demand_card: dict[str, Any]
    issues: list[ValidationIssue] = field(default_factory=list)
    assistant_findings: list[AssistantFinding] = field(default_factory=list)

    @property
    def status(self) -> str:
        if any(issue.severity == "blocker" for issue in self.issues):
            return "blocked_sensitive"
        if any(issue.severity == "error" for issue in self.issues):
            return "needs_revision"
        if self.assistant_findings:
            return "needs_revision"
        if self.demand_card.get("human_confirmed") is True:
            return "confirmed"
        return "ready_for_confirmation"

    def to_dict(self) -> dict[str, Any]:
        card = dict(self.demand_card)
        card["status"] = self.status
        card["validation_issues"] = [issue.to_dict() for issue in self.issues]
        card["assistant_findings"] = [
            finding.to_dict() for finding in self.assistant_findings
        ]
        return card


def build_demand_card(raw: dict[str, Any]) -> DemandCardResult:
    """Normalize user input into an S0 demand card and validate it.

    The function is deterministic by design. Future LLM output can be passed in
    as prefilled fields, but this function remains the final local gate.
    """

    card = _normalize(raw)
    issues = _validate(card)
    assistant_findings = _assistant_review(card) if not issues else []
    result = DemandCardResult(card, issues, assistant_findings)
    result.demand_card["status"] = result.status
    result.demand_card["sensitivity_check"] = _sensitivity_summary(issues)
    return result


def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    constraints = dict(raw.get("constraints") or {})
    source_input = dict(raw.get("source_input") or {})

    excluded = constraints.get("excluded_services")
    if not excluded:
        excluded = list(DEFAULT_EXCLUDED_SERVICES)

    card = {
        "schema_version": "s0.demand_card.v1",
        "run_id": raw.get("run_id") or _make_run_id(raw, now),
        "stage": "S0",
        "status": "draft",
        "created_at": raw.get("created_at") or now,
        "created_by": raw.get("created_by") or "unknown",
        "problem_statement": _clean_text(raw.get("problem_statement")),
        "current_approach": _clean_text(raw.get("current_approach")),
        "desired_outcome": _clean_text(raw.get("desired_outcome")),
        "business_domain": _clean_text(raw.get("business_domain")),
        "evaluation_priority": _clean_list(raw.get("evaluation_priority")),
        "constraints": {
            "excluded_services": excluded,
            "max_small_poc_usd": constraints.get(
                "max_small_poc_usd", DEFAULT_MAX_SMALL_POC_USD
            ),
            "no_sensitive_data": constraints.get("no_sensitive_data", True),
            "preferred_region": constraints.get("preferred_region", DEFAULT_REGION),
        },
        "success_criteria": _clean_list(raw.get("success_criteria")),
        "source_mode": _clean_text(raw.get("source_mode")).lower(),
        "source_input": source_input,
        "human_confirmed": bool(raw.get("human_confirmed", False)),
        "notes": _clean_text(raw.get("notes")),
    }
    return card


def _validate(card: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not card["problem_statement"]:
        issues.append(
            ValidationIssue(
                "missing_problem_statement",
                "S0 needs a problem statement before S1 can scan evidence.",
                "error",
            )
        )
    if not card["desired_outcome"]:
        issues.append(
            ValidationIssue(
                "missing_desired_outcome",
                "S0 needs the expected improvement or decision goal.",
                "error",
            )
        )
    if not card["success_criteria"]:
        issues.append(
            ValidationIssue(
                "missing_success_criteria",
                "At least one success criterion is required.",
                "error",
            )
        )
    if card["source_mode"] not in ALLOWED_SOURCE_MODES:
        issues.append(
            ValidationIssue(
                "invalid_source_mode",
                "source_mode must be one of: rss, url, paste, service.",
                "error",
            )
        )
    if card["source_mode"] == "url" and not card["source_input"].get("url"):
        issues.append(
            ValidationIssue("missing_url", "URL mode requires source_input.url.", "error")
        )

    issues.extend(_sensitive_findings(card))
    return issues


def _assistant_review(card: dict[str, Any]) -> list[AssistantFinding]:
    """Rule-based first implementation for the future LLM demand-card assistant.

    It flags common vague inputs so the GUI can ask a human to clarify before S1.
    """

    findings: list[AssistantFinding] = []
    problem = card["problem_statement"]
    outcome = card["desired_outcome"]

    if _is_vague(problem):
        findings.append(
            AssistantFinding(
                "vague_problem_statement",
                "The problem statement is too broad for a reliable radar run.",
                "What concrete workflow, system, or decision are you trying to improve?",
            )
        )
    if _is_vague(outcome):
        findings.append(
            AssistantFinding(
                "vague_desired_outcome",
                "The desired outcome is too broad to judge success.",
                "How should the result improve: speed, operations, security, integration, or user experience?",
            )
        )
    if card["source_mode"] == "url" and "aws.amazon.com" not in str(
        card["source_input"].get("url", "")
    ).lower():
        findings.append(
            AssistantFinding(
                "non_aws_url",
                "The URL is not clearly an AWS official source.",
                "Should S1 treat this as third-party context and search for official AWS documentation?",
            )
        )
    return findings


def _sensitive_findings(card: dict[str, Any]) -> list[ValidationIssue]:
    text = " ".join(
        str(value)
        for value in [
            card.get("problem_statement"),
            card.get("current_approach"),
            card.get("desired_outcome"),
            card.get("notes"),
            card.get("source_input"),
        ]
    )
    checks = [
        (
            "aws_access_key",
            re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
            "Input appears to contain an AWS access key.",
        ),
        (
            "private_key",
            re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
            "Input appears to contain a private key.",
        ),
        (
            "aws_secret_label",
            re.compile(r"aws(.{0,20})?(secret|secret_access_key)", re.IGNORECASE),
            "Input appears to mention an AWS secret value.",
        ),
        (
            "account_id",
            re.compile(r"\b\d{12}\b"),
            "Input appears to contain a 12-digit AWS account id.",
        ),
        (
            "private_ip",
            re.compile(
                r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b"
            ),
            "Input appears to contain a private IP address.",
        ),
    ]

    issues: list[ValidationIssue] = []
    for code, pattern, message in checks:
        if pattern.search(text):
            issues.append(ValidationIssue(code, message, "blocker"))
    return issues


def _sensitivity_summary(issues: list[ValidationIssue]) -> dict[str, Any]:
    flags = [issue.code for issue in issues if issue.severity == "blocker"]
    return {
        "status": "blocked" if flags else "passed",
        "flags": flags,
        "notes": "Sensitive input detected." if flags else "No blocking sensitive patterns detected.",
    }


def _is_vague(value: str) -> bool:
    if len(value.strip()) < 12:
        return True
    vague_terms = ["improve efficiency", "better", "optimize", "modernize", "faster"]
    lowered = value.lower()
    return any(term == lowered or lowered.endswith(term) for term in vague_terms)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _make_run_id(raw: dict[str, Any], created_at: str) -> str:
    seed = repr(sorted(raw.items())) + created_at
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
    day = created_at[:10].replace("-", "")
    return f"agentic-cloud-radar-{day}-{digest}"
