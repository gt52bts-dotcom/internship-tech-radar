"""S4: create validation artifacts without starting paid cloud work.

This local S4 implementation is a validator, not a deployer. It reads S3,
checks whether each recommended candidate can safely proceed, and records the
validation path. Paid PoC remains impossible unless a later explicit approval
request passes cost, Region, and approver checks.
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
        if any(item["validation_status"] == "paid_poc_ready_for_manual_start" for item in self.artifact["validated_candidates"]):
            return "ready_for_manual_paid_poc_review"
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
        "schema_version": "s4.validation.v1",
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
            "message": "No paid PoC approval was supplied; S4 will only produce low-risk validation artifacts.",
        }
    validation_type = str(approval_request.get("validation_type") or "low_risk_validation")
    if validation_type != "paid_poc":
        return {
            "status": "low_risk_requested",
            "validation_type": "low_risk_validation",
            "approved_by": approval_request.get("approved_by"),
            "automatic_poc_start": False,
            "message": "Request is limited to low-risk validation.",
        }
    approved_by = str(approval_request.get("approved_by") or "").strip()
    estimated_usd = approval_request.get("estimated_usd")
    approved_cost_ceiling_usd = approval_request.get("approved_cost_ceiling_usd")
    try:
        approved_cost = float(approved_cost_ceiling_usd if approved_cost_ceiling_usd is not None else estimated_usd)
    except (TypeError, ValueError):
        approved_cost = None
    max_cost = float((evaluate.get("policy") or {}).get("max_small_poc_usd", DEFAULT_MAX_SMALL_POC_USD))
    missing = []
    if not approved_by:
        missing.append("approved_by")
    if approved_cost is None:
        missing.append("approved_cost_ceiling_usd_or_estimated_usd")
    elif approved_cost > max_cost:
        missing.append("approved_cost_within_limit")
    return {
        "status": "paid_poc_requested" if not missing else "paid_poc_request_incomplete",
        "validation_type": "paid_poc",
        "approved_by": approved_by or None,
        "estimated_usd": float(estimated_usd) if isinstance(estimated_usd, (int, float)) else None,
        "approved_cost_ceiling_usd": approved_cost,
        "cost_basis": "human_approved_ceiling" if approved_cost_ceiling_usd is not None else "estimated_usd",
        "max_small_poc_usd": max_cost,
        "missing_or_failed_checks": missing,
        "automatic_poc_start": False,
        "message": "Passing this gate only marks a candidate ready for manual paid PoC review; S4 never starts resources automatically.",
    }


def _validate_candidate(candidate: dict[str, Any], approval: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    region = candidate.get("region_status") or {}
    paid_checks = _paid_poc_checks(candidate, approval, region, policy)
    evidence_checks = _evidence_checks(candidate)
    if not candidate.get("recommend_s4"):
        status = "not_validated_not_recommended"
        validation_type = "none"
    elif approval.get("validation_type") == "paid_poc" and all(check["passed"] for check in paid_checks):
        status = "paid_poc_ready_for_manual_start"
        validation_type = "paid_poc_review"
    else:
        status = "validated_low_risk"
        validation_type = "low_risk_validation"

    downgrade_reasons = [check["name"] for check in paid_checks if not check["passed"]]
    return {
        "candidate_id": candidate.get("candidate_id"),
        "title": candidate.get("title"),
        "validation_status": status,
        "validation_type": validation_type,
        "automatic_poc_start": False,
        "evidence_checks": evidence_checks,
        "paid_poc_checks": paid_checks,
        "downgrade_reasons": downgrade_reasons if status == "validated_low_risk" else [],
        "cleanup_status": "not_applicable_no_cloud_resources_created",
        "result_summary": _result_summary(status, downgrade_reasons),
        "limitations": _limitations(candidate, status),
    }


def _paid_poc_checks(
    candidate: dict[str, Any], approval: dict[str, Any], region: dict[str, Any], policy: dict[str, Any]
) -> list[dict[str, Any]]:
    approved_cost = approval.get("approved_cost_ceiling_usd")
    if approved_cost is None:
        approved_cost = approval.get("estimated_usd")
    max_cost = float(policy.get("max_small_poc_usd", DEFAULT_MAX_SMALL_POC_USD))
    return [
        {
            "name": "recommend_s4",
            "passed": bool(candidate.get("recommend_s4")),
            "detail": "S3 must recommend S4 before any validation path proceeds.",
        },
        {
            "name": "region_status_available",
            "passed": region.get("status") == "available_ap_southeast_1",
            "detail": "Paid PoC requires feature-level target Region evidence.",
        },
        {
            "name": "approved_cost_within_limit",
            "passed": isinstance(approved_cost, (int, float)) and float(approved_cost) <= max_cost,
            "detail": "Paid PoC needs a human-approved cost ceiling or estimate within the small-PoC cap.",
        },
        {
            "name": "approved_by_present",
            "passed": bool(approval.get("approved_by")),
            "detail": "Paid PoC requires a named human approver.",
        },
        {
            "name": "automatic_poc_start_false",
            "passed": approval.get("automatic_poc_start") is False,
            "detail": "S4 never starts paid resources automatically.",
        },
    ]


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
    if status == "paid_poc_ready_for_manual_start":
        return "All S4 paid-PoC checks passed, but no resources were started automatically."
    if status == "validated_low_risk":
        return "Low-risk validation artifact created; paid PoC is deferred or downgraded."
    return "Candidate was not recommended by S3, so S4 records limits only."


def _limitations(candidate: dict[str, Any], status: str) -> list[str]:
    limits = [
        "No AWS resources were created or modified by this S4 validator.",
        "No company data, production data, or private permissions were accessed.",
    ]
    if status != "paid_poc_ready_for_manual_start":
        limits.append("This is not a completed PoC; it is validation evidence for later review.")
    if (candidate.get("region_status") or {}).get("blocks_paid_poc"):
        limits.append("Paid PoC remains blocked until feature-level target Region evidence is available.")
    return limits


def _summary(validated: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "validated_count": len(validated),
        "low_risk_count": sum(1 for item in validated if item["validation_status"] == "validated_low_risk"),
        "paid_poc_ready_count": sum(
            1 for item in validated if item["validation_status"] == "paid_poc_ready_for_manual_start"
        ),
        "automatic_poc_start": False,
        "cloud_resources_created": False,
    }
