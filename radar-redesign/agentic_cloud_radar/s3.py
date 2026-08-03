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

from .costing import build_cost_quote


ALLOWED_S2_STATUSES = {"ready_for_human_shortlist"}
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
                "region_status": item.get("region_status"),
                "quote_status": (item.get("cost_estimate") or {}).get("status"),
                "expected_total_usd": quote.get("expected_total_usd"),
                "estimated_range_usd": quote.get("estimated_range_usd") or {},
                "recommended_approval_ceiling_usd": quote.get("recommended_approval_ceiling_usd"),
                "technically_eligible": bool(item.get("recommend_poc")),
                "blockers": list(item.get("governance_flags") or []),
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
            "approved_ceiling_usd",
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
                "adoption_prerequisites",
                "verifiability",
                "risk_and_stop_conditions",
            ],
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


def _evaluate_candidate(
    candidate: dict[str, Any],
    gate: dict[str, Any],
    compare: dict[str, Any],
    evaluated_at: str,
) -> dict[str, Any]:
    del gate
    dimensions = candidate.get("comparison_dimensions") or {}
    proposal = candidate.get("proposal_card") or {}
    coverage = candidate.get("evidence_coverage") or {}
    region = dimensions.get("target_region_eligibility") or {}
    unknowns = (dimensions.get("unknowns_and_next_validation_question") or {}).get("unknowns") or []
    stop_conditions = ((proposal.get("validation_design") or {}).get("stop_conditions") or [])[:]

    dimension_scores = {
        "technical_value": _technical_value_score(dimensions, coverage, proposal),
        "adoption_prerequisites": _adoption_prerequisites_score(dimensions, coverage, region),
        "verifiability": _verifiability_score(dimensions, proposal, coverage),
        "risk_and_stop_conditions": _risk_score(stop_conditions, unknowns),
    }
    weighted_score = round(
        sum(dimension_scores[name] * weight for name, weight in RUBRIC_WEIGHTS.items()),
        2,
    )
    governance_flags = _governance_flags(candidate, region)
    quote = build_cost_quote(
        candidate,
        str(compare.get("run_id") or "unknown-run"),
        region.get("target_region"),
        datetime.fromisoformat(evaluated_at),
    )
    poc_blockers = _poc_blockers(governance_flags, region, quote)
    recommend_poc = (
        weighted_score >= 3.75
        and not poc_blockers
    )
    poc_review_notes = _poc_review_notes(coverage, region, quote)

    return {
        "candidate_id": candidate.get("candidate_id"),
        "title": candidate.get("title"),
        "source_url": candidate.get("source_url"),
        "source_explanation": candidate.get("explanation") or {},
        "initial_claims": candidate.get("initial_claims") or [],
        "possible_application_contexts": candidate.get("possible_application_contexts") or [],
        "dimension_scores": dimension_scores,
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
    dimensions: dict[str, Any], coverage: dict[str, Any], region: dict[str, Any]
) -> int:
    score = 5
    if region.get("status") == "region_unknown":
        score -= 1
    if not coverage.get("official_pricing_linked"):
        score -= 1
    if not coverage.get("official_docs_linked"):
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


def _risk_score(stop_conditions: list[str], unknowns: list[str]) -> int:
    score = 5
    if not stop_conditions:
        score -= 2
    if len(unknowns) >= 4:
        score -= 1
    return max(score, 0)


def _governance_flags(candidate: dict[str, Any], region: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    title = str(candidate.get("title") or "").lower()
    if "bedrock" in title:
        flags.append("excluded_service_bedrock")
    if region.get("blocks_s3"):
        flags.append("region_blocks_s3")
    return flags


def _poc_blockers(governance_flags: list[str], region: dict[str, Any], quote: dict[str, Any]) -> list[str]:
    """Return the single set of blockers for a paid Skill 4 PoC."""

    blockers = [
        flag for flag in governance_flags if flag in {"excluded_service_bedrock", "region_blocks_s3"}
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
                f"- 報價狀態：{_display_status(quote_status)}",
                f"- 預期成本 USD：{option.get('expected_total_usd') if option.get('expected_total_usd') is not None else '未記錄'}",
                f"- 低/預期/高 USD：{_range_text(option.get('estimated_range_usd') or {})}",
                f"- 建議核准上限 USD：{option.get('recommended_approval_ceiling_usd') if option.get('recommended_approval_ceiling_usd') is not None else '未記錄'}",
                f"- 可部署 recipe：{'有，' + str(quote.get('recipe')) if has_recipe else '沒有或尚未登錄'}",
                f"- PoC blocker：{', '.join(blockers) if blockers else '無'}",
                f"- Review notes：{', '.join(candidate.get('poc_review_notes') or []) if candidate else '未記錄'}",
                f"- 是否值得交給 Cleo 決定進入 Skill 4：{'是' if technically_eligible else '否'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Cleo 需要回覆",
            "",
            "- 若同意 PoC：請回覆同意進入 Skill 4，並確認候選、核准上限、成功條件與 cleanup 範圍。",
            "- 若不同意 PoC：請回覆不進 Skill 4，並可指定要改評估標準、換候選或補證據。",
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


def _candidate_by_id(artifact: dict[str, Any], candidate_id: Any) -> dict[str, Any] | None:
    for candidate in artifact.get("evaluated_candidates") or []:
        if str(candidate.get("candidate_id") or "") == str(candidate_id or ""):
            return candidate
    return None


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
