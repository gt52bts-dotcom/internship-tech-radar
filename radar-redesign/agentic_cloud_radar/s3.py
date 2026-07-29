"""S3: score a human-shortlisted set of S2 proposal cards.

S3 is intentionally conservative. It only reads the S2 comparison artifact and
an explicit human shortlist request. It does not discover new sources, tune the
rubric per candidate, estimate unknown prices, or authorize a PoC.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


ALLOWED_S2_STATUSES = {"ready_for_human_shortlist"}
MAX_SHORTLIST_SIZE = 3
DEFAULT_MAX_SMALL_POC_USD = 3.0
RUBRIC_WEIGHTS = {
    "technical_value": 0.35,
    "adoption_prerequisites": 0.25,
    "verifiability": 0.25,
    "risk_and_stop_conditions": 0.15,
}


@dataclass(frozen=True)
class EvaluateIssue:
    code: str
    message: str
    severity: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "severity": self.severity}


@dataclass
class EvaluateResult:
    artifact: dict[str, Any]
    issues: list[EvaluateIssue] = field(default_factory=list)

    @property
    def status(self) -> str:
        if any(issue.severity == "blocker" for issue in self.issues):
            return "blocked_s2_not_usable"
        if any(issue.severity == "error" for issue in self.issues):
            return "needs_revision"
        if self.artifact["human_shortlist_gate"]["status"] != "provided":
            return "needs_human_shortlist"
        if not self.artifact["evaluated_candidates"]:
            return "no_selected_candidates_evaluated"
        return "evaluated"

    def to_dict(self) -> dict[str, Any]:
        payload = dict(self.artifact)
        payload["status"] = self.status
        payload["evaluation_issues"] = [issue.to_dict() for issue in self.issues]
        return payload


def build_evaluate(compare: dict[str, Any], shortlist_request: dict[str, Any] | None = None) -> EvaluateResult:
    """Build an S3 artifact from S2 and a human shortlist request."""

    issues = _validate_s2(compare)
    artifact = _base_artifact(compare, shortlist_request)
    if issues:
        return EvaluateResult(artifact, issues)

    gate = _human_shortlist_gate(shortlist_request)
    artifact["human_shortlist_gate"] = gate
    if gate["status"] != "provided":
        return EvaluateResult(artifact, issues)

    candidates_by_id = {str(candidate.get("candidate_id")): candidate for candidate in compare.get("candidates") or []}
    selected_ids = gate["selected_candidate_ids"]
    for selected_id in selected_ids:
        candidate = candidates_by_id.get(selected_id)
        if candidate is None:
            issues.append(EvaluateIssue("selected_candidate_not_found", f"{selected_id} is not present in S2.", "error"))
            continue
        artifact["evaluated_candidates"].append(_evaluate_candidate(candidate, gate, compare))

    artifact["evaluated_candidates"].sort(key=lambda item: (-item["weighted_score"], item["candidate_id"]))
    artifact["summary"] = _summary(artifact["evaluated_candidates"])
    return EvaluateResult(artifact, issues)


def _validate_s2(compare: dict[str, Any]) -> list[EvaluateIssue]:
    if compare.get("stage") != "S2" or compare.get("status") not in ALLOWED_S2_STATUSES:
        return [
            EvaluateIssue(
                "s2_not_usable",
                "S3 requires an S2 artifact with status ready_for_human_shortlist.",
                "blocker",
            )
        ]
    return []


def _base_artifact(compare: dict[str, Any], shortlist_request: dict[str, Any] | None) -> dict[str, Any]:
    policy = (shortlist_request or {}).get("policy") or {}
    return {
        "schema_version": "s3.evaluation.v1",
        "run_id": compare.get("run_id", "unknown-run"),
        "stage": "S3",
        "status": "draft",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "s2_artifact_ref": {
            "schema_version": compare.get("schema_version"),
            "stage": compare.get("stage"),
            "status": compare.get("status"),
            "compared_at": compare.get("compared_at"),
            "candidate_count": len(compare.get("candidates") or []),
        },
        "rubric": {
            "weights": RUBRIC_WEIGHTS,
            "fixed_weight_policy": "Weights are fixed for this S3 version and are not tuned per candidate.",
            "dimensions": [
                "technical_value",
                "adoption_prerequisites",
                "verifiability",
                "risk_and_stop_conditions",
            ],
            "cost_policy": "Cost is recorded for S4 budget checks only; it is not part of the technical score.",
        },
        "policy": {
            "max_small_poc_usd": float(policy.get("max_small_poc_usd", DEFAULT_MAX_SMALL_POC_USD)),
            "automatic_poc_start": False,
        },
        "human_shortlist_gate": {
            "status": "missing",
            "required_inputs": [
                "selected_candidate_ids, at most three",
                "problem_to_solve",
                "available_environment",
                "forbidden_data_and_permissions",
            ],
        },
        "evaluated_candidates": [],
        "summary": {},
    }


def _human_shortlist_gate(shortlist_request: dict[str, Any] | None) -> dict[str, Any]:
    if not shortlist_request:
        return {
            "status": "missing",
            "selected_candidate_ids": [],
            "required_inputs": [
                "selected_candidate_ids, at most three",
                "problem_to_solve",
                "available_environment",
                "forbidden_data_and_permissions",
            ],
            "message": "S3 stops until a human shortlist request is provided.",
        }

    selected_ids = [str(item).strip() for item in shortlist_request.get("selected_candidate_ids") or [] if str(item).strip()]
    missing = [
        field
        for field in ("problem_to_solve", "available_environment", "forbidden_data_and_permissions")
        if not str(shortlist_request.get(field) or "").strip()
    ]
    if not selected_ids:
        missing.append("selected_candidate_ids")
    if len(selected_ids) > MAX_SHORTLIST_SIZE:
        return {
            "status": "invalid",
            "selected_candidate_ids": selected_ids,
            "message": f"Human shortlist may contain at most {MAX_SHORTLIST_SIZE} candidates.",
            "missing_inputs": missing,
        }
    if missing:
        return {
            "status": "missing_required_context",
            "selected_candidate_ids": selected_ids,
            "message": "S3 requires problem, environment, and forbidden-boundary context before evaluation.",
            "missing_inputs": missing,
        }
    return {
        "status": "provided",
        "selected_candidate_ids": selected_ids,
        "problem_to_solve": str(shortlist_request.get("problem_to_solve")),
        "available_environment": str(shortlist_request.get("available_environment")),
        "forbidden_data_and_permissions": str(shortlist_request.get("forbidden_data_and_permissions")),
        "selected_by": str(shortlist_request.get("selected_by") or "human_unspecified"),
        "selection_reason": str(shortlist_request.get("selection_reason") or "Human selected these candidates for S3 evaluation."),
    }


def _evaluate_candidate(candidate: dict[str, Any], gate: dict[str, Any], compare: dict[str, Any]) -> dict[str, Any]:
    dimensions = candidate.get("comparison_dimensions") or {}
    proposal = candidate.get("proposal_card") or {}
    coverage = candidate.get("evidence_coverage") or {}
    region = dimensions.get("target_region_eligibility") or {}
    unknowns = (dimensions.get("unknowns_and_next_validation_question") or {}).get("unknowns") or []
    stop_conditions = ((proposal.get("validation_design") or {}).get("stop_conditions") or [])[:]

    dimension_scores = {
        "technical_value": _technical_value_score(dimensions, coverage, proposal),
        "adoption_prerequisites": _adoption_prerequisites_score(dimensions, coverage, region, gate),
        "verifiability": _verifiability_score(dimensions, proposal, coverage),
        "risk_and_stop_conditions": _risk_score(stop_conditions, unknowns, region),
    }
    weighted_score = round(
        sum(dimension_scores[name] * weight for name, weight in RUBRIC_WEIGHTS.items()),
        2,
    )
    confidence = _confidence(coverage, unknowns, gate)
    governance_flags = _governance_flags(candidate, region, gate)
    recommend_s4 = weighted_score >= 3.25 and confidence in {"medium", "high"} and not governance_flags
    if region.get("blocks_paid_poc"):
        stop_conditions.append("Paid PoC must wait for feature-level target Region evidence or be downgraded.")

    return {
        "candidate_id": candidate.get("candidate_id"),
        "title": candidate.get("title"),
        "source_url": candidate.get("source_url"),
        "dimension_scores": dimension_scores,
        "weighted_score": weighted_score,
        "confidence": confidence,
        "recommend_s4": recommend_s4,
        "recommendation_reason": _recommendation_reason(weighted_score, confidence, governance_flags),
        "cost_estimate": {
            "status": "unknown",
            "estimated_usd": None,
            "score_policy": "Cost is excluded from S3 score and must be bounded before paid S4 PoC.",
        },
        "region_status": {
            "target_region": region.get("target_region"),
            "status": region.get("status", "region_unknown"),
            "severity": region.get("severity", "warning"),
            "blocks_s3": bool(region.get("blocks_s3")),
            "blocks_paid_poc": bool(region.get("blocks_paid_poc", True)),
        },
        "governance_flags": governance_flags,
        "stop_conditions": _dedupe(stop_conditions),
        "s4_validation_path": _s4_validation_path(recommend_s4, region),
        "evidence_refs": {
            "source_url": candidate.get("source_url"),
            "linked_evidence_count": len((candidate.get("linked_evidence") or {}).get("linked_sources") or []),
            "evidence_limits": candidate.get("evidence_limits") or [],
        },
    }


def _technical_value_score(dimensions: dict[str, Any], coverage: dict[str, Any], proposal: dict[str, Any]) -> int:
    score = 1
    if (dimensions.get("source_backed_capabilities") or {}).get("status") == "source_excerpt_available":
        score += 1
    if coverage.get("official_ga_evidence"):
        score += 1
    if ((proposal.get("improvement_hypothesis") or {}).get("potential_vectors") or []):
        score += 1
    if (dimensions.get("technology_scope") or {}).get("services_detected"):
        score += 1
    return min(score, 5)


def _adoption_prerequisites_score(
    dimensions: dict[str, Any], coverage: dict[str, Any], region: dict[str, Any], gate: dict[str, Any]
) -> int:
    score = 5
    if region.get("status") == "region_unknown":
        score -= 1
    if not coverage.get("official_pricing_linked"):
        score -= 1
    if not coverage.get("official_docs_linked"):
        score -= 1
    if not gate.get("available_environment"):
        score -= 1
    if not (dimensions.get("environment_signals") or {}).get("source_indicated_contexts"):
        score -= 1
    return max(score, 0)


def _verifiability_score(dimensions: dict[str, Any], proposal: dict[str, Any], coverage: dict[str, Any]) -> int:
    score = 1
    validation = proposal.get("validation_design") or {}
    if validation.get("before_measurements") and validation.get("after_measurements"):
        score += 2
    if validation.get("minimum_success_evidence"):
        score += 1
    if coverage.get("primary_source_fetched"):
        score += 1
    return min(score, 5)


def _risk_score(stop_conditions: list[str], unknowns: list[str], region: dict[str, Any]) -> int:
    score = 5
    if not stop_conditions:
        score -= 2
    if len(unknowns) >= 4:
        score -= 1
    if region.get("blocks_paid_poc"):
        score -= 1
    return max(score, 0)


def _confidence(coverage: dict[str, Any], unknowns: list[str], gate: dict[str, Any]) -> str:
    verified = int(coverage.get("verified_dimension_count") or 0)
    if verified >= 5 and len(unknowns) <= 3 and gate.get("status") == "provided":
        return "high"
    if verified >= 3 and gate.get("status") == "provided":
        return "medium"
    return "low"


def _governance_flags(candidate: dict[str, Any], region: dict[str, Any], gate: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    title = str(candidate.get("title") or "").lower()
    if "bedrock" in title:
        flags.append("excluded_service_bedrock")
    forbidden = str(gate.get("forbidden_data_and_permissions") or "").lower()
    if not forbidden or forbidden in {"none", "n/a"}:
        flags.append("forbidden_boundary_not_specific")
    if region.get("blocks_s3"):
        flags.append("region_blocks_s3")
    return flags


def _s4_validation_path(recommend_s4: bool, region: dict[str, Any]) -> str:
    if not recommend_s4:
        return "not_recommended"
    if region.get("blocks_paid_poc"):
        return "low_risk_validation_only"
    return "eligible_for_low_risk_or_paid_poc_review"


def _recommendation_reason(weighted_score: float, confidence: str, governance_flags: list[str]) -> str:
    if governance_flags:
        return "S4 is not recommended until governance flags are resolved."
    if weighted_score < 3.25:
        return "S4 is not recommended because the weighted score is below the S3 threshold."
    if confidence == "low":
        return "S4 is not recommended because evidence confidence is low."
    return "Recommend S4 validation, starting with the lowest-risk path."


def _summary(evaluated: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "evaluated_count": len(evaluated),
        "recommend_s4_count": sum(1 for item in evaluated if item.get("recommend_s4")),
        "highest_score": max((item["weighted_score"] for item in evaluated), default=None),
        "automatic_poc_start": False,
    }


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value).strip()))
