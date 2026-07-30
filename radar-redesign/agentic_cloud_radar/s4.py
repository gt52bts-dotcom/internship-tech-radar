"""S4: create validation artifacts without starting cloud work.

This local S4 implementation is a validator, not a deployer. It reads S3,
checks whether each recommended candidate can safely proceed, and records the
validation path. A PoC remains impossible unless a later explicit approval
request passes the short human-approval and cost checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


ALLOWED_S3_STATUSES = {"evaluated"}
DEFAULT_MAX_SMALL_POC_USD = 3.0


@dataclass(frozen=True)
class ValidateIssue:
    code: str
    message: str
    severity: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "severity": self.severity}


@dataclass
class ValidateResult:
    artifact: dict[str, Any]
    issues: list[ValidateIssue] = field(default_factory=list)

    @property
    def status(self) -> str:
        if any(issue.severity == "blocker" for issue in self.issues):
            return "blocked_s3_not_usable"
        if any(issue.severity == "error" for issue in self.issues):
            return "needs_revision"
        if not self.artifact["validated_candidates"]:
            return "no_s4_candidates"
        if any(item["validation_status"] == "poc_ready_for_manual_start" for item in self.artifact["validated_candidates"]):
            return "ready_for_manual_poc_review"
        if any(item["validation_status"] == "validated_low_risk" for item in self.artifact["validated_candidates"]):
            return "validated_low_risk"
        return "validated_with_limits"

    def to_dict(self) -> dict[str, Any]:
        payload = dict(self.artifact)
        payload["status"] = self.status
        payload["validation_issues"] = [issue.to_dict() for issue in self.issues]
        return payload


def build_validate(evaluate: dict[str, Any], approval_request: dict[str, Any] | None = None) -> ValidateResult:
    """Build an S4 validation artifact from S3."""

    issues = _validate_s3(evaluate)
    artifact = _base_artifact(evaluate, approval_request)
    if issues:
        return ValidateResult(artifact, issues)

    approval = _approval_gate(evaluate, approval_request)
    artifact["approval_gate"] = approval
    for candidate in evaluate.get("evaluated_candidates") or []:
        artifact["validated_candidates"].append(_validate_candidate(candidate, approval, artifact["policy"]))

    artifact["summary"] = _summary(artifact["validated_candidates"])
    return ValidateResult(artifact, issues)


def _validate_s3(evaluate: dict[str, Any]) -> list[ValidateIssue]:
    if evaluate.get("stage") != "S3" or evaluate.get("status") not in ALLOWED_S3_STATUSES:
        return [
            ValidateIssue(
                "s3_not_usable",
                "S4 requires an S3 artifact with status evaluated.",
                "blocker",
            )
        ]
    return []


def _base_artifact(evaluate: dict[str, Any], approval_request: dict[str, Any] | None) -> dict[str, Any]:
    policy = evaluate.get("policy") or {}
    request_policy = (approval_request or {}).get("policy") or {}
    return {
        "schema_version": "s4.validation.v2",
        "run_id": evaluate.get("run_id", "unknown-run"),
        "stage": "S4",
        "status": "draft",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "s3_artifact_ref": {
            "schema_version": evaluate.get("schema_version"),
            "stage": evaluate.get("stage"),
            "status": evaluate.get("status"),
            "evaluated_at": evaluate.get("evaluated_at"),
            "evaluated_count": len(evaluate.get("evaluated_candidates") or []),
        },
        "policy": {
            "max_small_poc_usd": float(
                request_policy.get("max_small_poc_usd", policy.get("max_small_poc_usd", DEFAULT_MAX_SMALL_POC_USD))
            ),
            "automatic_poc_start": False,
        },
        "approval_gate": {},
        "validated_candidates": [],
        "summary": {},
    }


def _approval_gate(evaluate: dict[str, Any], approval_request: dict[str, Any] | None) -> dict[str, Any]:
    if not approval_request:
        return {
            "status": "not_requested",
            "validation_type": "low_risk_validation",
            "automatic_poc_start": False,
            "message": "No PoC approval was supplied; S4 will only produce low-risk validation artifacts.",
        }
    default_type = "poc" if approval_request.get("deployment_authorized") is True else "low_risk_validation"
    requested_type = str(approval_request.get("validation_type") or default_type)
    validation_type = "poc" if requested_type in {"poc", "paid_poc"} else requested_type
    if validation_type != "poc":
        return {
            "status": "low_risk_requested",
            "validation_type": "low_risk_validation",
            "approved_by": approval_request.get("approved_by"),
            "automatic_poc_start": False,
            "message": "Request is limited to low-risk validation.",
        }
    approved_by = str(approval_request.get("approved_by") or "").strip()
    estimated_usd = approval_request.get("estimated_usd")
    max_cost = float((evaluate.get("policy") or {}).get("max_small_poc_usd", DEFAULT_MAX_SMALL_POC_USD))
    approved_cost_ceiling_usd = approval_request.get("approved_cost_ceiling_usd", max_cost)
    try:
        approved_cost = float(approved_cost_ceiling_usd if approved_cost_ceiling_usd is not None else estimated_usd)
    except (TypeError, ValueError):
        approved_cost = None
    missing = []
    if not approved_by:
        missing.append("approved_by")
    if approved_cost is None:
        missing.append("approved_cost_ceiling_usd_or_estimated_usd")
    elif approved_cost > max_cost:
        missing.append("approved_cost_within_limit")
    return {
        "status": "poc_requested" if not missing else "poc_request_incomplete",
        "validation_type": "poc",
        "approved_by": approved_by or None,
        "estimated_usd": float(estimated_usd) if isinstance(estimated_usd, (int, float)) else None,
        "approved_cost_ceiling_usd": approved_cost,
        "cost_basis": (
            "human_approved_ceiling"
            if "approved_cost_ceiling_usd" in approval_request
            else "default_sandbox_ceiling"
        ),
        "max_small_poc_usd": max_cost,
        "missing_or_failed_checks": missing,
        "automatic_poc_start": False,
        "message": "Passing this gate only marks a candidate ready for manual PoC review; S4 never starts resources automatically.",
    }


def _validate_candidate(candidate: dict[str, Any], approval: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    poc_checks = _poc_checks(candidate, approval, policy)
    evidence_checks = _evidence_checks(candidate)
    recommend_low_risk = _recommend_low_risk_validation(candidate)
    eligible_poc_review = _eligible_for_poc_review(candidate)
    if not recommend_low_risk:
        status = "not_validated_not_recommended"
        validation_type = "none"
    elif approval.get("validation_type") == "poc" and all(check["passed"] for check in poc_checks):
        status = "poc_ready_for_manual_start"
        validation_type = "poc_review"
    else:
        status = "validated_low_risk"
        validation_type = "low_risk_validation"

    downgrade_reasons = [check["name"] for check in poc_checks if not check["passed"]]
    return {
        "candidate_id": candidate.get("candidate_id"),
        "title": candidate.get("title"),
        "validation_status": status,
        "validation_type": validation_type,
        "recommend_low_risk_validation": recommend_low_risk,
        "eligible_for_poc_review": eligible_poc_review,
        "eligible_for_paid_poc_review": eligible_poc_review,
        "automatic_poc_start": False,
        "evidence_checks": evidence_checks,
        "poc_checks": poc_checks,
        "paid_poc_checks": poc_checks,
        "downgrade_reasons": downgrade_reasons if status == "validated_low_risk" else [],
        "cleanup_status": "not_applicable_no_cloud_resources_created",
        "result_summary": _result_summary(status, downgrade_reasons),
        "limitations": _limitations(candidate, status),
    }


def _poc_checks(
    candidate: dict[str, Any], approval: dict[str, Any], policy: dict[str, Any]
) -> list[dict[str, Any]]:
    approved_cost = approval.get("approved_cost_ceiling_usd")
    if approved_cost is None:
        approved_cost = approval.get("estimated_usd")
    max_cost = float(policy.get("max_small_poc_usd", DEFAULT_MAX_SMALL_POC_USD))
    return [
        {
            "name": "eligible_for_poc_review",
            "passed": _eligible_for_poc_review(candidate),
            "detail": "S3 must mark the public evidence ready for PoC review.",
        },
        {
            "name": "approved_cost_within_limit",
            "passed": isinstance(approved_cost, (int, float)) and float(approved_cost) <= max_cost,
            "detail": "PoC uses the fixed small-cost ceiling unless a lower ceiling is supplied.",
        },
        {
            "name": "approved_by_present",
            "passed": bool(approval.get("approved_by")),
            "detail": "PoC requires a named human approver.",
        },
        {
            "name": "automatic_poc_start_false",
            "passed": approval.get("automatic_poc_start") is False,
            "detail": "S4 never starts resources automatically.",
        },
    ]


def _recommend_low_risk_validation(candidate: dict[str, Any]) -> bool:
    """Read the v2 decision while remaining compatible with S3 v1 artifacts."""

    if "recommend_low_risk_validation" in candidate:
        return bool(candidate.get("recommend_low_risk_validation"))
    return bool(candidate.get("recommend_s4"))


def _eligible_for_poc_review(candidate: dict[str, Any]) -> bool:
    """Read the simplified v3 PoC decision with v2/v1 compatibility."""

    if "eligible_for_poc_review" in candidate:
        return bool(candidate.get("eligible_for_poc_review"))
    if "eligible_for_paid_poc_review" in candidate:
        return bool(candidate.get("eligible_for_paid_poc_review"))
    return bool(candidate.get("recommend_s4"))


def _evidence_checks(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    refs = candidate.get("evidence_refs") or {}
    return [
        {
            "name": "source_url_present",
            "passed": bool(refs.get("source_url")),
            "detail": refs.get("source_url") or "missing",
        },
        {
            "name": "stop_conditions_present",
            "passed": bool(candidate.get("stop_conditions")),
            "detail": f"{len(candidate.get('stop_conditions') or [])} stop conditions recorded.",
        },
        {
            "name": "score_and_confidence_present",
            "passed": candidate.get("weighted_score") is not None and bool(candidate.get("confidence")),
            "detail": f"score={candidate.get('weighted_score')}, confidence={candidate.get('confidence')}",
        },
    ]


def _result_summary(status: str, downgrade_reasons: list[str]) -> str:
    if status == "poc_ready_for_manual_start":
        return "All S4 PoC checks passed, but no resources were started automatically."
    if status == "validated_low_risk":
        return "Low-risk validation artifact created; PoC review is deferred."
    return "Candidate was not recommended for low-risk validation by S3, so S4 records limits only."


def _limitations(candidate: dict[str, Any], status: str) -> list[str]:
    limits = [
        "No AWS resources were created or modified by this S4 validator.",
        "No protected or production data was accessed.",
    ]
    if status != "poc_ready_for_manual_start":
        limits.append("This is not a completed PoC; it is validation evidence for later review.")
    if (candidate.get("region_status") or {}).get("status") == "region_unknown":
        limits.append("Target Region support remains a deployment-time review note.")
    return limits


def _summary(validated: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "validated_count": len(validated),
        "low_risk_count": sum(1 for item in validated if item["validation_status"] == "validated_low_risk"),
        "poc_ready_count": sum(
            1 for item in validated if item["validation_status"] == "poc_ready_for_manual_start"
        ),
        "paid_poc_ready_count": sum(
            1 for item in validated if item["validation_status"] == "poc_ready_for_manual_start"
        ),
        "automatic_poc_start": False,
        "cloud_resources_created": False,
    }
