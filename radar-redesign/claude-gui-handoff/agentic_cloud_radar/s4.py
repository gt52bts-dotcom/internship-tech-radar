"""S4: gate one controlled, paid PoC without starting it automatically."""

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
        if any(item["validation_status"] == "awaiting_poc_approval" for item in self.artifact["validated_candidates"]):
            return "awaiting_poc_approval"
        return "no_poc_candidates"

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
        "schema_version": "s4.validation.v3",
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
            "status": "required",
            "validation_type": "poc",
            "automatic_poc_start": False,
            "message": "Skill 4 is a controlled paid PoC. A named approval and cost ceiling are required before deployment.",
        }
    approved_by = str(approval_request.get("approved_by") or "").strip()
    selected_id = str(approval_request.get("selected_candidate_id") or "").strip()
    selected = next(
        (
            item
            for item in evaluate.get("evaluated_candidates") or []
            if str(item.get("candidate_id") or "") == selected_id
        ),
        None,
    )
    quote = ((selected or {}).get("cost_estimate") or {}).get("quote") or {}
    estimated_usd = approval_request.get("estimated_usd", quote.get("expected_total_usd"))
    max_cost = float((evaluate.get("policy") or {}).get("max_small_poc_usd", DEFAULT_MAX_SMALL_POC_USD))
    quote_ceiling = quote.get("recommended_approval_ceiling_usd")
    human_ceiling = approval_request.get("approved_cost_ceiling_usd")
    approved_cost_ceiling_usd = approval_request.get(
        "approved_cost_ceiling_usd",
        quote_ceiling if isinstance(quote_ceiling, (int, float)) else max_cost,
    )
    try:
        approved_cost = float(approved_cost_ceiling_usd if approved_cost_ceiling_usd is not None else estimated_usd)
    except (TypeError, ValueError):
        approved_cost = None
    missing = []
    if not approved_by:
        missing.append("approved_by")
    if approved_cost is None:
        missing.append("approved_cost_ceiling_usd_or_estimated_usd")
    effective_ceiling = _effective_cost_ceiling(quote_ceiling, approved_cost, max_cost)
    if effective_ceiling is None:
        missing.append("effective_cost_ceiling")
    elif approved_cost is not None and approved_cost > effective_ceiling:
        missing.append("approved_cost_within_limit")
    return {
        "status": "poc_requested" if not missing else "poc_request_incomplete",
        "validation_type": "poc",
        "approved_by": approved_by or None,
        "deployment_authorized": approval_request.get("deployment_authorized") is True,
        "region_warning_acknowledged": approval_request.get("region_warning_acknowledged") is True,
        "estimated_usd": float(estimated_usd) if isinstance(estimated_usd, (int, float)) else None,
        "approved_cost_ceiling_usd": approved_cost,
        "effective_cost_ceiling_usd": effective_ceiling,
        "cost_ceiling_policy": {
            "rule": "effective ceiling is the minimum of Skill 3 recommended ceiling, human approved ceiling, and built-in small-cost ceiling.",
            "skill3_recommended_approval_ceiling_usd": quote_ceiling,
            "human_approved_ceiling_usd": human_ceiling,
            "built_in_small_cost_ceiling_usd": max_cost,
        },
        "cost_quote_id": quote.get("quote_id"),
        "cost_quote_status": quote.get("status") or "not_available",
        "cost_basis": (
            "human_approved_ceiling"
            if "approved_cost_ceiling_usd" in approval_request
            else "quoted_high_scenario_ceiling"
            if isinstance(quote_ceiling, (int, float))
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
    recommend_poc = _recommend_poc(candidate)
    if not recommend_poc:
        status = "not_recommended_for_poc"
        validation_type = "none"
    elif approval.get("validation_type") == "poc" and all(check["passed"] for check in poc_checks):
        status = "poc_ready_for_manual_start"
        validation_type = "poc"
    else:
        status = "awaiting_poc_approval"
        validation_type = "poc"

    downgrade_reasons = [check["name"] for check in poc_checks if not check["passed"]]
    return {
        "candidate_id": candidate.get("candidate_id"),
        "title": candidate.get("title"),
        "validation_status": status,
        "validation_type": validation_type,
        "recommend_poc": recommend_poc,
        "automatic_poc_start": False,
        "evidence_checks": evidence_checks,
        "poc_checks": poc_checks,
        "pending_checks": downgrade_reasons if status == "awaiting_poc_approval" else [],
        "cleanup_status": "not_applicable_no_cloud_resources_created",
        "cost_estimate": candidate.get("cost_estimate"),
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
    region_status = (candidate.get("region_status") or {}).get("status")
    target_region = (candidate.get("region_status") or {}).get("target_region") or "ap-southeast-1"
    region_acknowledged = approval.get("region_warning_acknowledged") is True
    region_passed = region_status == f"available_{str(target_region).replace('-', '_')}" or (
        region_status == "region_unknown" and region_acknowledged
    )
    return [
        {
            "name": "s3_recommends_poc",
            "passed": _recommend_poc(candidate),
            "detail": "Skill 3 must recommend this candidate for the controlled PoC.",
        },
        {
            "name": "cost_quote_ready",
            "passed": (candidate.get("cost_estimate") or {}).get("status") == "estimated",
            "detail": "Skill 3 must provide an estimated public-price PoC quote before Skill 4.",
        },
        {
            "name": "approved_cost_within_limit",
            "passed": isinstance(approved_cost, (int, float))
            and isinstance(approval.get("effective_cost_ceiling_usd"), (int, float))
            and float(approved_cost) <= float(approval["effective_cost_ceiling_usd"])
            and float(approved_cost) <= max_cost,
            "detail": "Effective ceiling is min(Skill 3 recommended, human approved, built-in sandbox ceiling).",
        },
        {
            "name": "target_region_confirmed_or_acknowledged",
            "passed": region_passed,
            "detail": (
                f"Region status is {region_status or 'unknown'} for {target_region}; "
                "region_unknown requires region_warning_acknowledged=true before a paid PoC."
            ),
        },
        {
            "name": "approved_by_present",
            "passed": bool(approval.get("approved_by")),
            "detail": "PoC requires a named human approver.",
        },
        {
            "name": "deployment_authorized",
            "passed": approval.get("deployment_authorized") is True,
            "detail": "PoC requires explicit deployment_authorized=true from the named approver.",
        },
        {
            "name": "automatic_poc_start_false",
            "passed": approval.get("automatic_poc_start") is False,
            "detail": "S4 never starts resources automatically.",
        },
    ]


def _recommend_poc(candidate: dict[str, Any]) -> bool:
    """Read the single v4 PoC recommendation, retaining old artifacts as input."""

    if "recommend_poc" in candidate:
        return bool(candidate.get("recommend_poc"))
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
        {
            "name": "cost_quote_recorded",
            "passed": bool((candidate.get("cost_estimate") or {}).get("quote_id")),
            "detail": (
                f"quote_id={(candidate.get('cost_estimate') or {}).get('quote_id')}, "
                f"status={(candidate.get('cost_estimate') or {}).get('status') or 'unknown'}"
            ),
        },
    ]


def _result_summary(status: str, downgrade_reasons: list[str]) -> str:
    if status == "poc_ready_for_manual_start":
        return "All S4 PoC checks passed, but no resources were started automatically."
    if status == "awaiting_poc_approval":
        return "Skill 3 recommends this PoC, but named approval or the approved cost ceiling is still missing."
    return "Skill 3 did not recommend this candidate for the controlled PoC."


def _limitations(candidate: dict[str, Any], status: str) -> list[str]:
    limits = [
        "No AWS resources were created or modified by this S4 validator.",
        "No protected or production data was accessed.",
    ]
    if status != "poc_ready_for_manual_start":
        limits.append("This is not a completed PoC; deployment remains blocked until the pending checks pass.")
    if (candidate.get("region_status") or {}).get("status") == "region_unknown":
        limits.append("Target Region support is not verified; paid deployment requires explicit region_warning_acknowledged=true.")
    return limits


def _effective_cost_ceiling(*values: Any) -> float | None:
    numeric = []
    for value in values:
        if isinstance(value, (int, float)):
            numeric.append(float(value))
    if not numeric:
        return None
    return min(numeric)


def _summary(validated: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "validated_count": len(validated),
        "awaiting_poc_approval_count": sum(
            1 for item in validated if item["validation_status"] == "awaiting_poc_approval"
        ),
        "poc_ready_count": sum(
            1 for item in validated if item["validation_status"] == "poc_ready_for_manual_start"
        ),
        "automatic_poc_start": False,
        "cloud_resources_created": False,
    }
