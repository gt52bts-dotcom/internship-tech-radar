"""S3: score one human-selected S2 proposal card.

S3 is intentionally conservative. It only reads the S2 comparison artifact and
an explicit human selection request. It does not discover new sources, tune the
rubric for the selected candidate, or authorize a PoC. Cost quotes may come from
a registered recipe or a reusable generic usage model, but deployable Skill 4
recipes are still checked separately.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

from .rubric import (
    RUBRIC_CRITERIA,
    VETO_THRESHOLDS,
    WEIGHTS,
    score_adoption_prerequisites,
    score_reversibility,
    score_risk_and_stop_conditions,
    score_technical_value,
    score_verifiability,
)
from .s4_recipes import select_recipe
from .costing import build_cost_quote


ALLOWED_S2_STATUSES = {"ready_for_human_shortlist"}
DEFAULT_MAX_SMALL_POC_USD = 10.0
RUBRIC_WEIGHTS = WEIGHTS  # 單一來源在 rubric.py


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
        if not self.artifact["evaluated_candidates"]:
            return "no_candidates_evaluated"
        return "awaiting_poc_decision"

    def to_dict(self) -> dict[str, Any]:
        payload = dict(self.artifact)
        payload["status"] = self.status
        payload["evaluation_issues"] = [issue.to_dict() for issue in self.issues]
        return payload


def build_evaluate(compare: dict[str, Any], candidate_filter: dict[str, Any] | None = None) -> EvaluateResult:
    """Score and quote every S2 candidate so one merged human gate can decide.

    S3 no longer requires a prior selection step.  It evaluates each candidate
    recorded by S2 and produces a complete PoC quote for each, so the single
    downstream gate can weigh value and estimated cost at the same time.
    ``candidate_filter`` stays available for old callers that want to restrict
    the evaluation to specific candidate ids; it is not a human approval.
    """

    issues = _validate_s2(compare)
    artifact = _base_artifact(compare, candidate_filter)
    if issues:
        return EvaluateResult(artifact, issues)

    candidates = list(compare.get("candidates") or [])
    requested_ids = [
        str(item).strip()
        for item in (candidate_filter or {}).get("selected_candidate_ids") or []
        if str(item).strip()
    ]
    if requested_ids:
        by_id = {str(item.get("candidate_id")): item for item in candidates}
        candidates = []
        for requested in requested_ids:
            match = by_id.get(requested)
            if match is None:
                issues.append(
                    EvaluateIssue("selected_candidate_not_found", f"{requested} is not present in S2.", "error")
                )
                continue
            candidates.append(match)

    for candidate in candidates:
        artifact["evaluated_candidates"].append(
            _evaluate_candidate(candidate, {}, compare, artifact["evaluated_at"])
        )

    artifact["evaluated_candidates"].sort(key=lambda item: (-item["weighted_score"], item["candidate_id"]))
    artifact["cost_quote_reports"] = [_cost_quote_report(item) for item in artifact["evaluated_candidates"]]
    artifact["summary"] = _summary(artifact["evaluated_candidates"])
    artifact["poc_decision_gate"] = _poc_decision_gate(artifact["evaluated_candidates"])
    return EvaluateResult(artifact, issues)


def _poc_decision_gate(evaluated: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the single merged gate: pick one candidate AND authorize the PoC."""

    options = []
    for item in evaluated:
        quote = (item.get("cost_estimate") or {}).get("quote") or {}
        options.append(
            {
                "candidate_id": item.get("candidate_id"),
                "title": item.get("title"),
                "weighted_score": item.get("weighted_score"),
                "max_score": 5,
                "dimension_scores": item.get("dimension_scores") or {},
                "dimension_score_details": item.get("dimension_score_details") or {},
                "region_status": item.get("region_status"),
                "quote_status": (item.get("cost_estimate") or {}).get("status"),
                "expected_total_usd": quote.get("expected_total_usd"),
                "estimated_range_usd": quote.get("estimated_range_usd") or {},
                "recommended_approval_ceiling_usd": quote.get("recommended_approval_ceiling_usd"),
                "technically_eligible": bool(item.get("recommend_poc")),
                "blockers": list(item.get("governance_flags") or []),
                "recipe_decision": item.get("poc_recipe") or {},
                "can_enter_skill4": bool((item.get("s4_readiness") or {}).get("can_enter_skill4")),
            }
        )
    return {
        "status": "awaiting_human_decision",
        "gate_type": "single_merged_value_and_cost_gate",
        "decides": [
            "which single candidate proceeds to Skill 4, if any",
            "whether the estimated PoC cost is worth spending",
        ],
        "required_outputs": [
            "selected_candidate_id",
            "approved_by",
            "approved_cost_ceiling_usd",
        ],
        "rule": "Skill 4 never starts without this gate. Technical eligibility is not approval.",
        "options": options,
    }


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


def _base_artifact(compare: dict[str, Any], candidate_filter: dict[str, Any] | None) -> dict[str, Any]:
    policy = (candidate_filter or {}).get("policy") or {}
    return {
        "schema_version": "s3.evaluation.v4",
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
                "verifiability",
                "adoption_prerequisites",
                "risk_and_stop_conditions",
                "reversibility_and_cleanup",
            ],
            "score_policy": "Rubric scores the nature of the technology and the PoC, not whether S1/S2 happened to collect many documents. Evidence coverage may create blockers or review notes, but it does not add score points.",
            "cost_policy": "Every evaluated candidate receives a complete PoC quote so the merged gate can compare value against estimated cost. Level A uses a registered recipe; Level B uses a reusable generic usage model; Level C incomplete quotes block PoC recommendation. Cost is not part of the technical score.",
        },
        "policy": {
            "max_small_poc_usd": float(policy.get("max_small_poc_usd", DEFAULT_MAX_SMALL_POC_USD)),
            "automatic_poc_start": False,
        },
        "evaluation_mode": "public_evidence",
        "poc_decision_gate": {"status": "not_built", "options": []},
        "evaluated_candidates": [],
        "cost_quote_reports": [],
        "summary": {},
    }


def _s4_readiness(decision: dict[str, Any], recommend_poc: bool) -> dict[str, Any]:
    """Say plainly whether this candidate may proceed, and what the next step is.

    A candidate can be worth evaluating and still be unable to deploy. Reporting
    those two facts separately stops "值得評估" from being read as "可以部署".
    """

    registered = bool(decision.get("deployable_recipe_registered"))
    if registered and recommend_poc:
        return {
            "can_enter_skill4": True,
            "readiness_status": "ready_for_skill4",
            "technical_assessment_zh": "技術上值得評估。",
            "reason_zh": decision.get("reason_zh", ""),
            "next_step_zh": "進行人工核准與 Skill 4 部署前檢查。",
        }
    if registered and not recommend_poc:
        return {
            "can_enter_skill4": False,
            "readiness_status": "score_or_blocker_failed",
            "technical_assessment_zh": "已有可部署 recipe，但技術資格門檻未通過。",
            "reason_zh": "加權分未達門檻，或存在阻斷條件。",
            "next_step_zh": "補足證據後重新評估，不是建立 AWS 資源。",
        }
    return {
        "can_enter_skill4": False,
        "readiness_status": "missing_deployable_recipe",
        "technical_assessment_zh": (
            "技術上值得評估，但目前不能進 Skill 4。" if recommend_poc
            else "技術資格門檻亦未通過，且目前不能進 Skill 4。"
        ),
        "reason_zh": decision.get("reason_zh", ""),
        "next_step_zh": decision.get(
            "next_step_zh", "下一步是建立或補齊專用 recipe，不是建立 AWS 資源。"
        ),
        "authoring_template": decision.get(
            "authoring_template", "docs/s4-recipe-authoring-template.md"
        ),
    }


def _evaluate_candidate(
    candidate: dict[str, Any],
    gate: dict[str, Any],
    compare: dict[str, Any],
    evaluated_at: str,
) -> dict[str, Any]:
    del gate
    recipe_decision = select_recipe(candidate)
    dimensions = candidate.get("comparison_dimensions") or {}
    proposal = candidate.get("proposal_card") or {}
    coverage = candidate.get("evidence_coverage") or {}
    region = dimensions.get("target_region_eligibility") or {}
    unknowns = (dimensions.get("unknowns_and_next_validation_question") or {}).get("unknowns") or []
    stop_conditions = ((proposal.get("validation_design") or {}).get("stop_conditions") or [])[:]

    governance_flags = _governance_flags(candidate, region)
    quote = build_cost_quote(
        candidate,
        str(compare.get("run_id") or "unknown-run"),
        region.get("target_region"),
        datetime.fromisoformat(evaluated_at),
    )
    score_details = _score_candidate(
        candidate,
        dimensions,
        proposal,
        region,
        stop_conditions,
        unknowns,
        quote,
        recipe_decision,
    )
    dimension_scores = {
        name: detail["score"]
        for name, detail in score_details.items()
    }
    weighted_score = round(
        sum(dimension_scores[name] * weight for name, weight in RUBRIC_WEIGHTS.items()),
        2,
    )
    vetoed = [
        name for name, floor in VETO_THRESHOLDS.items()
        if dimension_scores.get(name, 5) <= floor
    ]
    poc_blockers = _poc_blockers(governance_flags, region, quote)
    poc_blockers.extend(f"veto_{name}" for name in vetoed)
    if not recipe_decision.get("deployable_recipe_registered"):
        poc_blockers.append("no_deployable_recipe")
    recommend_poc = (
        weighted_score >= 3.75
        and not poc_blockers
    )
    poc_review_notes = _poc_review_notes(coverage, region, quote)

    return {
        "candidate_id": candidate.get("candidate_id"),
        "title": candidate.get("title"),
        "source_url": candidate.get("source_url"),
        "poc_recipe": recipe_decision,
        "s4_readiness": _s4_readiness(recipe_decision, recommend_poc),
        "source_explanation": candidate.get("explanation") or {},
        "initial_claims": candidate.get("initial_claims") or [],
        "possible_application_contexts": candidate.get("possible_application_contexts") or [],
        "dimension_scores": dimension_scores,
        "dimension_details": score_details,
        "veto_violations": vetoed,
        "poc_blockers": poc_blockers,
        "information_provenance": _information_provenance(candidate, quote, recipe_decision),
        "dimension_score_details": score_details,
        "weighted_score": weighted_score,
        "recommend_poc": recommend_poc,
        "recommend_s4_compatibility": {
            "deprecated": True,
            "maps_to": "recommend_poc",
            "value": recommend_poc,
            "reason": "Kept only for readers of older artifacts; new consumers must use recommend_poc.",
        },
        "recommendation_reason": _recommendation_reason(
            weighted_score,
            poc_blockers,
            recommend_poc,
            poc_review_notes,
        ),
        "cost_estimate": {
            "status": quote["status"],
            "estimated_usd": quote.get("expected_total_usd"),
            "range_usd": quote.get("estimated_range_usd"),
            "recommended_approval_ceiling_usd": quote.get("recommended_approval_ceiling_usd"),
            "quote_id": quote["quote_id"],
            "quote": quote,
            "score_policy": "Cost is excluded from S3 score and is checked separately before deployment.",
        },
        "region_status": {
            "target_region": region.get("target_region"),
            "status": region.get("status", "region_unknown"),
            "severity": region.get("severity", "warning"),
            "blocks_s3": bool(region.get("blocks_s3")),
            "requires_region_confirmation": bool(region.get("blocks_paid_poc", True)),
        },
        "governance_flags": governance_flags,
        "poc_review_notes": poc_review_notes,
        "assessment_scope": {
            "mode": "public_evidence",
            "company_fit": "not_assessed",
            "custom_environment_required": False,
        },
        "stop_conditions": _dedupe(stop_conditions),
        "s4_path": "poc" if recommend_poc else "not_recommended",
        "evidence_refs": {
            "source_url": candidate.get("source_url"),
            "linked_evidence_count": len((candidate.get("linked_evidence") or {}).get("linked_sources") or []),
            "evidence_limits": candidate.get("evidence_limits") or [],
        },
    }


def _score_candidate(
    candidate: dict[str, Any],
    dimensions: dict[str, Any],
    proposal: dict[str, Any],
    region: dict[str, Any],
    stop_conditions: list[str],
    unknowns: list[str],
    quote: dict[str, Any],
    recipe_decision: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    explanation = candidate.get("source_explanation") or candidate.get("explanation") or {}
    raw = {
        "technical_value": score_technical_value(explanation, proposal, dimensions),
        "verifiability": score_verifiability(proposal, recipe_decision, explanation),
        "adoption_prerequisites": score_adoption_prerequisites(region, recipe_decision, quote),
        "risk_and_stop_conditions": score_risk_and_stop_conditions(stop_conditions, unknowns, quote),
        "reversibility_and_cleanup": score_reversibility(quote, recipe_decision),
    }
    return {
        name: _score_detail(name, score, reason)
        for name, (score, reason) in raw.items()
    }


def _score_detail(name: str, score: int, reason_zh: str) -> dict[str, Any]:
    weight = WEIGHTS[name]
    return {
        "score": score,
        "weight": weight,
        "weighted_points": round(score * weight, 2),
        "reason_zh": reason_zh,
    }


def _governance_flags(candidate: dict[str, Any], region: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    title = str(candidate.get("title") or "").lower()
    if "bedrock" in title:
        flags.append("excluded_service_bedrock")
    if _touches_screen_or_user_session(candidate):
        flags.append("compliance_review_required")
    if region.get("blocks_s3"):
        flags.append("region_blocks_s3")
    return flags


# 觀察畫面或驅動使用者工作階段的能力，不論由哪個產品提供都可能接觸個資，
# 因此旗標依能力訊號判定，而不是依產品名稱。
SCREEN_OR_SESSION_TERMS = (
    "desktop", "screen", "screenshot", "streaming session", "remote session",
    "computer vision", "computer input", "operate applications", "桌面", "畫面", "工作階段",
)


def _touches_screen_or_user_session(candidate: dict[str, Any]) -> bool:
    explanation = candidate.get("source_explanation") or candidate.get("explanation") or {}
    significance = explanation.get("significance") or {}
    text = " ".join(
        str(value or "")
        for value in (
            candidate.get("title"), candidate.get("summary"),
            significance.get("after"), significance.get("difference"),
            *[str(item.get("point") or "") for item in explanation.get("key_points") or []],
        )
    ).lower()
    return any(term in text for term in SCREEN_OR_SESSION_TERMS)


def _poc_blockers(governance_flags: list[str], region: dict[str, Any], quote: dict[str, Any]) -> list[str]:
    """Return the single set of blockers for a paid Skill 4 PoC."""

    blockers = [
        flag for flag in governance_flags
        if flag in {
            "excluded_service_bedrock",
            "region_blocks_s3",
            "production_data_required",
            "unsafe_permissions",
            "compliance_review_required",
        }
    ]
    if quote.get("status") != "estimated":
        blockers.append("poc_quote_not_ready")
    return blockers


def _poc_review_notes(coverage: dict[str, Any], region: dict[str, Any], quote: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    if region.get("status") == "region_unknown":
        notes.append("target_region_support_not_verified")
    if not coverage.get("official_pricing_linked"):
        notes.append("official_pricing_not_linked")
    if quote.get("status") != "estimated":
        notes.append("cost_quote_incomplete")
    return notes


def _recommendation_reason(
    weighted_score: float,
    poc_blockers: list[str],
    recommend_poc: bool,
    poc_review_notes: list[str],
) -> str:
    if poc_blockers:
        return "Skill 4 PoC is not recommended until its blockers are resolved: " + ", ".join(_dedupe(poc_blockers)) + "."
    if weighted_score < 3.75:
        return "Skill 4 PoC is not recommended because the weighted score is below the 3.75 threshold."
    if poc_review_notes:
        return "Recommend Skill 4 PoC. Review notes: " + ", ".join(_dedupe(poc_review_notes)) + "."
    return "Recommend Skill 4 PoC; the quote is ready for named-human approval."


def _summary(evaluated: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "evaluated_count": len(evaluated),
        "recommend_poc_count": sum(1 for item in evaluated if item.get("recommend_poc")),
        "highest_score": max((item["weighted_score"] for item in evaluated), default=None),
        "automatic_poc_start": False,
    }


def _cost_quote_report(evaluated: dict[str, Any]) -> dict[str, Any]:
    quote = ((evaluated.get("cost_estimate") or {}).get("quote") or {})
    status = str(quote.get("status") or "unknown")
    status_label = _display_status(status)
    quote_id = str(quote.get("quote_id") or "unknown")
    report_id = f"{quote_id}-skill3-quote"
    lines = [
        f"# Skill 3 PoC 報價單：{evaluated.get('title') or '未記錄'}",
        "",
        f"- Quote ID：{quote_id}",
        f"- 狀態：{status_label}",
        f"- Run ID：{quote.get('run_id') or '未記錄'}",
        f"- Candidate ID：{quote.get('candidate_id') or evaluated.get('candidate_id') or '未記錄'}",
        f"- 目標區域：{quote.get('target_region') or '未記錄'}",
        f"- 報價性質：{_display_status(quote.get('quote_kind') or 'non_binding_public_price_estimate')}",
        f"- 即時 AWS Pricing API：{'是' if quote.get('live_pricing_api_used') else '否'}",
        f"- 正式採購報價：{'是' if quote.get('formal_procurement_quote_ready') else '否'}",
        f"- 有效期限：{quote.get('valid_until') or '未記錄'}",
        "",
    ]
    if status == "estimated":
        price_range = quote.get("estimated_range_usd") or {}
        lines.extend(
            [
                f"- 預期費用 USD：{quote.get('expected_total_usd')}",
                f"- 低/中/高情境 USD：{price_range.get('low')} / {price_range.get('expected')} / {price_range.get('high')}",
                f"- 建議核准上限 USD：{quote.get('recommended_approval_ceiling_usd')}",
                f"- Recipe：{quote.get('recipe') or '未記錄'}",
                "",
                "## 明細",
                "",
            ]
        )
        expected = (quote.get("scenarios") or {}).get("expected") or {}
        for item in expected.get("line_items") or []:
            lines.append(
                f"- {item.get('item')}: qty={item.get('quantity')} {item.get('quantity_unit')}, "
                f"rate={item.get('rate_usd')} {item.get('rate_unit')}, subtotal={item.get('subtotal_usd')} USD"
            )
        lines.extend(["", "## 來源", ""])
        for source in quote.get("sources") or []:
            lines.append(f"- {source.get('purpose')}: {source.get('url')}")
    else:
        missing = quote.get("missing_inputs") or []
        lines.extend(
            [
                "## 為什麼不能給金額",
                "",
                f"- 原因：{quote.get('pricing_basis') or '未記錄報價依據。'}",
                f"- 缺少輸入：{', '.join(str(item) for item in missing) if missing else '未記錄'}",
                "- 這仍然是一張 Skill 3 報價單，但它的結論是目前不能報價，不能進入實際 Skill 4 付費 PoC。",
            ]
        )
    return {
        "report_id": report_id,
        "quote_id": quote.get("quote_id"),
        "candidate_id": evaluated.get("candidate_id"),
        "status": status,
        "markdown": "\n".join(lines) + "\n",
    }



def _information_provenance(
    candidate: dict[str, Any], quote: dict[str, Any], recipe_decision: dict[str, Any]
) -> dict[str, Any]:
    """記錄報告中每一區的資訊由哪個階段產生。

    一份評估報告混合三種來源：原文說了什麼（S1）、比較後整理出什麼（S2）、
    以及 S3 自己算出來的分數與報價。讀報告的人若分不出來，就會把 S3 的推導
    當成 AWS 的原文陳述——那正是這套流程最想避免的事。
    """

    explanation = candidate.get("source_explanation") or candidate.get("explanation") or {}
    return {
        "S1": {
            "說明": "原文與解釋層。內容取自公開文章，未經 S3 加工。",
            "欄位": [
                name for name, present in (
                    ("原文重點 key_points", bool(explanation.get("key_points"))),
                    ("以前／現在／差別 significance", bool(explanation.get("significance"))),
                    ("實作架構草案 implementation_architecture",
                     bool(explanation.get("implementation_architecture"))),
                    ("可能應用場景 possible_application_contexts",
                     bool(explanation.get("possible_application_contexts"))),
                ) if present
            ],
        },
        "S2": {
            "說明": "比較與提案卡。由 S1 候選整理而成，不含評分。",
            "欄位": [
                name for name, present in (
                    ("比較構面 comparison_dimensions", bool(candidate.get("comparison_dimensions"))),
                    ("提案卡 proposal_card", bool(candidate.get("proposal_card"))),
                    ("證據涵蓋 evidence_coverage", bool(candidate.get("evidence_coverage"))),
                    ("區域證據 region_status", bool(candidate.get("region_status"))),
                ) if present
            ],
        },
        "S3": {
            "說明": "本階段自行產生。分數依固定準則計算，報價依公開牌價估算，兩者皆非原文陳述。",
            "欄位": [
                "各構面分數與理由 dimension_details", "加權總分 weighted_score",
                "否決判定 veto_violations",
                *(["成本估算 cost_estimate"] if quote else []),
                *(["recipe 判定 poc_recipe"] if recipe_decision else []),
                "可否進入 Skill 4 s4_readiness",
            ],
        },
    }


def _render_criteria_breakdown(candidate: dict[str, Any] | None) -> list[str]:
    """逐項列出構面得分、權重與判定理由。單一加權數字無法被質疑，細目才能。"""

    details = (candidate or {}).get("dimension_details") or {}
    if not details:
        return []
    lines = [
        "- 評分細項（權重與門檻於評分前宣告，不依候選調整）：", "",
        "    | 構面 | 得分 | 權重 | 加權 | 否決門檻 | 判定理由 |",
        "    | --- | :---: | ---: | ---: | :---: | --- |",
    ]
    for name, spec in RUBRIC_CRITERIA.items():
        detail = details.get(name) or {}
        score = detail.get("score")
        floor = spec["veto_at_or_below"]
        flag = "　**已觸發**" if floor is not None and score is not None and score <= floor else ""
        lines.append(
            f"    | {spec['label']} | {score} / 5 | {spec['weight']} | {detail.get('weighted_points')} | "
            f"{('<= ' + str(floor)) if floor is not None else '—'}{flag} | {detail.get('reason_zh', '')} |"
        )
    lines.append("")
    vetoed = (candidate or {}).get("veto_violations") or []
    if vetoed:
        labels = [RUBRIC_CRITERIA[v]["label"] for v in vetoed if v in RUBRIC_CRITERIA]
        lines.append(
            "- **否決構面**：" + "、".join(labels)
            + "。此類缺陷無法由其他構面補償，加權總分不論多高皆不得進入 Skill 4。"
        )
    lines.append("- 完整判定條件見 `docs/評分準則.md`。")
    return lines


def _render_information_provenance(candidate: dict[str, Any] | None) -> list[str]:
    """標示報告中哪些資訊來自 S1／S2，哪些是 S3 自己產生的。"""

    provenance = (candidate or {}).get("information_provenance") or {}
    if not provenance:
        return []
    lines = ["", "## 本報告的資訊來源", "", "| 階段 | 內容 | 說明 |", "| :---: | --- | --- |"]
    for stage in ("S1", "S2", "S3"):
        block = provenance.get(stage) or {}
        fields = "、".join(block.get("欄位") or []) or "（無）"
        lines.append(f"| {stage} | {fields} | {block.get('說明', '')} |")
    lines.extend([
        "",
        "> S1 與 S2 的內容取自公開來源或其整理；S3 的分數與報價是本階段依固定準則推導，"
        "不是原文陳述，也不是 AWS 的承諾。",
    ])
    return lines


def render_poc_decision_report(artifact: dict[str, Any]) -> str:
    """Render the Skill 3 human decision report shown before any Skill 4 PoC."""

    gate = artifact.get("poc_decision_gate") or {}
    options = list(gate.get("options") or [])
    lines = [
        "# Skill 3 PoC 決策報告",
        "",
        f"- Run ID：{artifact.get('run_id') or '未記錄'}",
        f"- 狀態：{_display_status(artifact.get('status'))}",
        "- PoC 門檻：Skill 3 加權分 >= 3.75 / 5、沒有 PoC blocker、報價狀態為已完成估算、Skill 4 有可部署 recipe。",
        "- 人工關卡：即使達標，也必須由 Cleo 明確同意候選、成本上限、成功條件與 cleanup 範圍，Skill 4 才能開始。",
        "- 本報告不會建立 AWS 資源，也不是部署核准。",
        "",
        "## 這篇文章在講什麼",
        "",
    ]
    _append_article_explanation(lines, artifact)
    value_lines = _poc_value_section(artifact)
    if value_lines:
        lines.extend(value_lines)
    lines.extend(
        [
            "",
            "## PoC 最小系統架構圖",
            "",
            "- HTML 版報告會直接內嵌 GPT-style PNG 架構圖，協助決策者理解 Skill 4 會建立與驗證的最小 PoC 資源。",
            "- 生成圖片仍需人工 QA：檢查小字、服務名稱、箭頭方向與資源範圍；圖片本身不是部署證據或 Console review 證據。",
            "",
        ]
    )
    lines.extend(
        [
            "",
            "## PoC 判斷",
            "",
        ]
    )
    if not options:
        lines.append("- 尚無可判斷候選。")
    for index, option in enumerate(options, start=1):
        quote_status = option.get("quote_status") or "unknown"
        score = option.get("weighted_score")
        blockers = list(option.get("blockers") or [])
        candidate = _candidate_by_id(artifact, option.get("candidate_id"))
        quote = ((candidate.get("cost_estimate") or {}).get("quote") or {}) if candidate else {}
        has_recipe = _has_deployable_recipe(quote)
        meets_score = isinstance(score, (int, float)) and score >= 3.75
        technically_eligible = bool(option.get("technically_eligible")) and has_recipe
        lines.extend(
            [
                f"### {index}. {option.get('title') or '未命名候選'}",
                "",
                f"- Candidate ID：{option.get('candidate_id') or '未記錄'}",
                f"- Skill 3 分數：{score if score is not None else '未記錄'} / 5",
                f"- 分數是否達標：{'是' if meets_score else '否'}",
                *_render_criteria_breakdown(candidate),
                f"- 報價狀態：{_display_status(quote_status)}",
                f"- 預期成本 USD：{option.get('expected_total_usd') if option.get('expected_total_usd') is not None else '未記錄'}",
                f"- 低/預期/高 USD：{_range_text(option.get('estimated_range_usd') or {})}",
                f"- 建議核准上限 USD：{option.get('recommended_approval_ceiling_usd') if option.get('recommended_approval_ceiling_usd') is not None else '未記錄'}",
                f"- 可部署 recipe：{'有，' + str(quote.get('recipe')) if has_recipe else '沒有或尚未登錄'}",
                f"- PoC blocker：{', '.join(blockers) if blockers else '無'}",
                f"- Review notes：{', '.join(candidate.get('poc_review_notes') or []) if candidate else '未記錄'}",
                f"- 是否值得交給 Cleo 決定進入 Skill 4：{'是' if technically_eligible else '否'}",
                f"- 目前可否進入 Skill 4：{'可以' if technically_eligible else ('不可以，分數或 blocker 未達標' if has_recipe else '不可以，缺少可部署 recipe')}",
                "",
            ]
        )
        lines.extend(_score_breakdown_lines(candidate))
    first = _candidate_by_id(artifact, (options[0] or {}).get("candidate_id")) if options else None
    lines.extend(_render_information_provenance(first))
    lines.append("")
    deployable_options = [
        option for option in options
        if option.get("technically_eligible") and (option.get("recipe_decision") or {}).get("deployable_recipe_registered")
    ]
    lines.extend(["## Cleo 需要回覆", ""])
    if deployable_options:
        lines.extend(
            [
                "- 若同意 PoC：請回覆同意進入 Skill 4，並確認候選、核准上限、成功條件與 cleanup 範圍。",
                "- 若不同意 PoC：請回覆不進 Skill 4，並可指定要改評估標準、換候選或補證據。",
            ]
        )
    else:
        # Offering "同意進入 Skill 4" when no candidate has a deployable recipe
        # would invite an approval that the deployment gate then refuses.
        lines.extend(
            [
                "- 目前不建議進 Skill 4：本輪沒有任何候選同時通過分數門檻、PoC blocker、報價與可部署 recipe 條件。",
                "- 下一步是先修正分數或 blocker 的根因；如果是缺 recipe 才補 recipe，如果是分數不足就不要建立 AWS 資源。",
                "- Cleo 仍可要求重評，但不應把「有 recipe」解讀成「可以部署」。",
            ]
        )
    return "\n".join(lines) + "\n"


def render_poc_decision_report_html(artifact: dict[str, Any], architecture_image_path: Path | None = None) -> str:
    """Render the human-facing Skill 3 decision report as self-contained HTML."""

    markdown = render_poc_decision_report(artifact)
    image_html = _architecture_image_html(architecture_image_path)
    body_lines: list[str] = []
    in_list = False
    for line in markdown.splitlines():
        if line.startswith("# "):
            if in_list:
                body_lines.append("</ul>")
                in_list = False
            body_lines.append(f"<h1>{escape(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            if in_list:
                body_lines.append("</ul>")
                in_list = False
            body_lines.append(f"<h2>{escape(line[3:].strip())}</h2>")
            if line[3:].strip() == "PoC 最小系統架構圖":
                body_lines.append(image_html)
        elif line.startswith("### "):
            if in_list:
                body_lines.append("</ul>")
                in_list = False
            body_lines.append(f"<h3>{escape(line[4:].strip())}</h3>")
        elif line.startswith("- "):
            if not in_list:
                body_lines.append("<ul>")
                in_list = True
            body_lines.append(f"<li>{escape(line[2:].strip())}</li>")
        elif not line.strip():
            if in_list:
                body_lines.append("</ul>")
                in_list = False
        else:
            if in_list:
                body_lines.append("</ul>")
                in_list = False
            body_lines.append(f"<p>{escape(line.strip())}</p>")
    if in_list:
        body_lines.append("</ul>")
    body = "\n".join(body_lines)
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>Skill 3 PoC 決策報告</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans TC","Microsoft JhengHei",sans-serif;line-height:1.65;color:#1f2937;max-width:1180px;margin:32px auto;padding:0 28px;background:#fff;}}
h1{{font-size:32px;margin:0 0 20px;color:#111827;}} h2{{font-size:26px;margin:34px 0 14px;border-bottom:1px solid #e5e7eb;padding-bottom:8px;}} h3{{font-size:21px;margin:24px 0 8px;}} ul{{padding-left:24px;}} li{{margin:4px 0;}} figure{{margin:18px 0 28px;}} figure img{{display:block;width:100%;height:auto;border:1px solid #d1d5db;border-radius:8px;box-shadow:0 2px 10px rgba(15,23,42,.08);}} figcaption{{font-size:14px;color:#6b7280;margin-top:8px;text-align:center;}} .notice{{border:1px solid #f59e0b;background:#fffbeb;color:#92400e;border-radius:8px;padding:12px 14px;margin:12px 0 24px;}}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def _architecture_image_html(image_path: Path | None) -> str:
    if not image_path:
        return (
            '<div class="notice">尚未嵌入架構圖 PNG。請先用 image generation 產生 GPT-style '
            "架構圖，再以 <code>--decision-report-image</code> 重新輸出 HTML。</div>"
        )
    data = image_path.read_bytes()
    suffix = image_path.suffix.lower()
    mime = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png"
    encoded = base64.b64encode(data).decode("ascii")
    alt = escape(image_path.stem.replace("-", " "))
    return f'<figure><img src="data:{mime};base64,{encoded}" alt="{alt}"><figcaption>{alt}</figcaption></figure>'


def _append_article_explanation(lines: list[str], artifact: dict[str, Any]) -> None:
    candidates = artifact.get("evaluated_candidates") or []
    if not candidates:
        lines.append("- 尚無候選文章可摘要。")
        return
    for index, candidate in enumerate(candidates, start=1):
        explanation = candidate.get("source_explanation") or {}
        significance = explanation.get("significance") or {}
        architecture = explanation.get("implementation_architecture") or {}
        key_points = list(explanation.get("key_points") or [])
        lines.extend(
            [
                f"### {index}. {candidate.get('title') or '未命名候選'}",
                "",
            ]
        )
        if significance:
            lines.extend(
                [
                    f"- 以前：{significance.get('before') or '原文未整理出明確以前狀態。'}",
                    f"- 現在：{significance.get('after') or '原文未整理出明確現在狀態。'}",
                    f"- 差別：{significance.get('difference') or '原文未整理出明確差異。'}",
                ]
            )
        else:
            claims = [str(item).strip() for item in candidate.get("initial_claims") or [] if str(item).strip()]
            if claims:
                lines.append(f"- 摘要：{claims[0]}")
            else:
                lines.append("- 摘要：S1/S2 尚未保留可用的文章解釋，需回查來源。")
        if key_points:
            lines.append("- 原文重點：")
            for point in key_points[:3]:
                lines.append(f"  - {point.get('point')}")
        flow = architecture.get("data_flow")
        if flow:
            lines.append(f"- 推導的最小架構：{flow}")
        unstated = architecture.get("unstated_but_required_components") or []
        if unstated:
            names = [str(item.get("name") or "").strip() for item in unstated if str(item.get("name") or "").strip()]
            if names:
                lines.append(f"- 原文未明講但 PoC 需要確認：{', '.join(names)}")


def _poc_value_section(artifact: dict[str, Any]) -> list[str]:
    gate = artifact.get("poc_decision_gate") or {}
    options = list(gate.get("options") or [])
    if not options:
        return []
    lines = ["", "## PoC 可以額外提供什麼價值", ""]
    for index, option in enumerate(options, start=1):
        candidate = _candidate_by_id(artifact, option.get("candidate_id")) or {}
        title = option.get("title") or candidate.get("title") or f"候選 {index}"
        recipe = str((option.get("recipe_decision") or {}).get("recipe_id") or "")
        cost = option.get("estimated_usd")
        lines.extend([f"### {index}. {title}", ""])
        lines.append(
            "- Skill 3 已經能回答：這篇新聞在解決什麼問題、可能帶來什麼技術價值、需要哪些 AWS 元件，以及用公開牌價估算小型 PoC 大約會花多少錢。"
        )
        if recipe:
            lines.extend(
                [
                    "- Skill 4 PoC 的額外價值：把 Skill 3 的文件推論轉成可檢查的 AWS runtime facts，確認資源真的能建立、驗證、盤點與清除。",
                    "- 它能提供 reviewer 會追問的證據：實際資源清單、權限面、成功條件、cleanup 結果，而不是只看架構圖與估價。",
                ]
            )
        else:
            lines.append(
                "- 目前沒有可部署 recipe，因此 PoC 的下一步價值不是建立 AWS 資源，而是先補齊 recipe、成本模型、成功條件與 cleanup 範圍。"
            )
        if cost is not None:
            lines.append(
                f"- 對這次決策的意義：用預期成本 USD {cost} 換取實際可行性與治理證據，"
                "幫 Cleo 判斷這篇新聞是否值得進一步投資。"
            )
        lines.append("")
    return lines


def _candidate_by_id(artifact: dict[str, Any], candidate_id: Any) -> dict[str, Any] | None:
    for candidate in artifact.get("evaluated_candidates") or []:
        if str(candidate.get("candidate_id") or "") == str(candidate_id or ""):
            return candidate
    return None


def _score_breakdown_lines(candidate: dict[str, Any] | None) -> list[str]:
    if not candidate:
        return []
    details = candidate.get("dimension_score_details") or {}
    if not details:
        return []
    lines = ["#### 評分細項", ""]
    for key in RUBRIC_WEIGHTS:
        detail = details.get(key) or {}
        score = detail.get("score")
        weight = detail.get("weight", RUBRIC_WEIGHTS[key])
        weighted = detail.get("weighted_points")
        reason = detail.get("reason_zh") or "未記錄評分理由。"
        lines.append(
            f"- {_score_label(key)}：{score} / 5，權重 {weight:.2f}，加權 {weighted}。{reason}"
        )
    lines.append("")
    return lines


def _score_label(key: str) -> str:
    labels = {
        "technical_value": "技術能力",
        "verifiability": "證據可驗證性",
        "adoption_prerequisites": "導入前置條件",
        "risk_and_stop_conditions": "可控制性與停止機制",
        "reversibility_and_cleanup": "可逆性與終止",
    }
    return labels.get(key, key)


def _has_deployable_recipe(quote: dict[str, Any]) -> bool:
    recipe = str(quote.get("recipe") or "")
    if not recipe or recipe == "generic_usage_model":
        return False
    return quote.get("deployable_recipe_registered", True) is not False


def _range_text(value: dict[str, Any]) -> str:
    if not value:
        return "未記錄"
    return f"{value.get('low')} / {value.get('expected')} / {value.get('high')}"


def _display_status(value: Any) -> str:
    labels = {
        "estimated": "已完成估算",
        "incomplete": "估價資料不足",
        "needs_registered_cost_model": "缺少已註冊成本模型",
        "non_binding_public_price_estimate": "非正式公開牌價估算",
        "awaiting_poc_decision": "等待 Cleo 決定是否進入 PoC",
        "unknown": "未記錄",
    }
    text = str(value or "unknown")
    return labels.get(text, text)


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value).strip()))
