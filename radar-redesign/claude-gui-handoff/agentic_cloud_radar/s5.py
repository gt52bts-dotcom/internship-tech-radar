"""Skill 5: render only recorded S1-S4 evidence into a professional report.

This module deliberately does not fetch sources or infer missing facts.  It
turns the immutable stage artifacts into one JSON report model, one Markdown
document, and one GUI-ready view model.  A renderer may change presentation,
but it must not invent a claim absent from these inputs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_report(
    scan: dict[str, Any],
    compare: dict[str, Any] | None = None,
    evaluate: dict[str, Any] | None = None,
    validate: dict[str, Any] | None = None,
    runtime: dict[str, Any] | None = None,
    billing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a source-bound Skill 5 artifact from the available stage artifacts."""

    inputs = {"S1": scan, "S2": compare, "S3": evaluate, "S4": validate}
    if runtime:
        inputs["S4 runtime"] = runtime
    if billing:
        inputs["Billing"] = billing
    issues = _input_issues(inputs)
    if (
        runtime
        and runtime.get("status") == "cleanup_verified"
        and not _is_abort_cleanup(runtime)
        and _runtime_requires_screenshot(runtime)
        and not _console_screenshot_count(runtime)
    ):
        issues.append("missing_console_screenshot_metadata")
    if (
        runtime
        and runtime.get("status") == "cleanup_verified"
        and not _is_abort_cleanup(runtime)
        and _runtime_requires_screenshot(runtime)
        and not _console_display_channel_confirmed(runtime)
    ):
        issues.append("missing_console_display_channel_confirmation")
    run_id = str(scan.get("run_id") or "unknown-run")
    evaluated = list((evaluate or {}).get("evaluated_candidates") or [])
    selected = evaluated[0] if evaluated else _first_candidate(compare)
    report_candidate = _merge_candidate_details(scan, compare, selected)
    validation = _matching_candidate(validate, selected.get("candidate_id") if selected else None)
    status = _report_status(issues, runtime)
    report = {
        "schema_version": "s5.report.v1",
        "stage": "S5",
        "run_id": run_id,
        "reported_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "report_type": "final" if status == "final" else "closed_without_console_review" if status == "final_without_console_review" else "interim",
        "input_contract": {
            "rule": "Only S1, S2, S3, and S4 artifacts may support report claims; missing evidence is unknown.",
            "stages_received": [name for name, artifact in inputs.items() if artifact],
        },
        "input_issues": issues,
        "candidate": _candidate_summary(report_candidate),
        "conclusion": _conclusion(selected, runtime),
        "news_summary": _news_application_summary(report_candidate),
        "evaluation": _evaluation_summary(selected),
        "cost_quote": _cost_quote(selected),
        "cost_reconciliation": _cost_reconciliation(selected, billing),
        "pre_cleanup_usage_snapshot": _pre_cleanup_usage_snapshot(runtime),
        "validation": _validation_summary(validation, runtime),
        "verified_facts": _verified_facts(scan, compare, selected, runtime, billing),
        "unknown_or_not_verified": _unknowns(compare, selected, validation, runtime, billing),
        "future_work": _future_work(selected, runtime, billing),
        "reviewer_questions": _reviewer_questions(selected, runtime, billing),
        "related_topics": _related_topics(report_candidate, compare, selected),
        "stage_evidence": _stage_evidence(scan, compare, evaluate, validate, runtime, billing, selected, status),
        "funnel": _funnel(scan, compare, evaluate, validate),
        "evidence_ledger": _evidence_ledger(scan, compare, selected, runtime, billing),
    }
    report["markdown"] = render_markdown(report)
    report["gui_model"] = build_gui_model(report)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    """Render a portable Markdown report without adding any new assertions."""

    candidate = report["candidate"]
    lines = [
        f"# 技術驗證報告｜{candidate['title'] or 'unknown'}",
        "",
        f"- 報告狀態：{_display_status(report['report_type'])}",
        f"- Run ID：{report['run_id']}",
        f"- 來源：{candidate['source_url'] or 'unknown'}",
        "",
        "## 新聞摘要：應用面優勢",
        "",
        f"> {report['news_summary']['text']}",
        "",
        "## 評估摘要",
        "",
        "| 指標 | 結果 |",
        "| --- | --- |",
    ]
    for label, value in report["evaluation"]["rows"]:
        lines.append(f"| {label} | {value} |")
    lines.extend(_render_cost_quote(report["cost_quote"]))
    lines.extend(_render_cost_reconciliation(report["cost_reconciliation"]))
    lines.extend(_render_pre_cleanup_usage_snapshot(report["pre_cleanup_usage_snapshot"]))
    lines.extend(["", "## 技術驗證", "", "| 檢查 | 狀態 |", "| --- | --- |"])
    for label, value in report["validation"]["rows"]:
        lines.append(f"| {label} | {value} |")
    lines.extend(["", "### 技術驗證狀態", ""])
    lines.extend(f"- {item}" for item in report["verified_facts"] or ["unknown"])
    lines.extend(["", "## 尚未驗證或證據不足", ""])
    lines.extend(f"- {item}" for item in report["unknown_or_not_verified"] or ["unknown"])
    lines.extend(["", "## Future work", ""])
    lines.extend(f"- {item}" for item in report["future_work"] or ["尚無額外 Future work。"])
    lines.extend(["", "## Reviewer questions", ""])
    lines.extend(f"- {item}" for item in report["reviewer_questions"] or ["尚無額外 reviewer question。"])
    lines.extend(["", "## 延伸閱讀關鍵字", ""])
    lines.extend(f"- {item}" for item in report["related_topics"] or ["未記錄"])
    lines.extend(["", "## S1-S5 階段證據", "", "| 階段 | 狀態 | 證據 |", "| --- | --- | --- |"])
    for entry in report["stage_evidence"]:
        lines.append(f"| {entry['stage']} | {_display_status(entry['status'])} | {entry['evidence']} |")
    lines.extend(["", "## 證據來源表", "", "| 敘述 | 類型 | 狀態 | 證據 |", "| --- | --- | --- | --- |"])
    for entry in report["evidence_ledger"]:
        lines.append(f"| {entry['claim']} | {entry['type']} | {_display_status(entry['status'])} | {entry['source']} |")
    return "\n".join(lines) + "\n"


def build_gui_model(report: dict[str, Any]) -> dict[str, Any]:
    """Expose stable UI data so a frontend never parses Markdown."""

    checks = [{"label": label, "status": value} for label, value in report["validation"]["rows"]]
    dimensions = report["evaluation"].get("dimensions") or {}
    return {
        "header": {
            "title": report["candidate"]["title"],
            "source_url": report["candidate"]["source_url"],
            "report_type": report["report_type"],
            "report_type_label": _display_status(report["report_type"]),
            "conclusion": report["conclusion"],
            "news_summary": report["news_summary"],
        },
        "score": {
            "weighted_score": report["evaluation"].get("weighted_score"),
            "confidence": report["evaluation"].get("confidence"),
            "dimensions": dimensions,
        },
        "cost_quote": {**report["cost_quote"], "status_label": _display_status(report["cost_quote"].get("status"))},
        "cost_reconciliation": {
            **report["cost_reconciliation"],
            "status_label": _display_status(report["cost_reconciliation"].get("status")),
        },
        "pre_cleanup_usage_snapshot": {
            **report["pre_cleanup_usage_snapshot"],
            "status_label": _usage_snapshot_status_label(report["pre_cleanup_usage_snapshot"].get("status")),
        },
        "console_review": _gui_console_review(report),
        "validation_checks": checks,
        "verified_facts": report["verified_facts"],
        "unknown_or_not_verified": report["unknown_or_not_verified"],
        "future_work": report["future_work"],
        "reviewer_questions": report["reviewer_questions"],
        "related_topics": report["related_topics"],
        "stage_evidence": report["stage_evidence"],
        "evidence_ledger": report["evidence_ledger"],
        "funnel": report["funnel"],
    }


def _gui_console_review(report: dict[str, Any]) -> dict[str, Any]:
    """Keep screenshot metadata available to an authenticated review UI."""

    ledger = report.get("evidence_ledger") or []
    evidence_entry = next(
        (entry for entry in ledger if entry.get("claim") == "Infrastructure Composer Console review"),
        None,
    )
    return {
        "status": next((item[1] for item in report["validation"]["rows"] if item[0] == "AWS Console review"), "unknown"),
        "screenshot_status": next((item[1] for item in report["validation"]["rows"] if item[0] == "Console 截圖證據"), "not_recorded"),
        "evidence_recorded": evidence_entry is not None,
        "privacy": "Render screenshot files only through an authenticated GUI or the active conversation; Git artifacts retain metadata only.",
    }


def _input_issues(inputs: dict[str, dict[str, Any] | None]) -> list[str]:
    run_ids = {str(value.get("run_id") or "") for value in inputs.values() if value}
    issues = [f"missing_{name.lower().replace(' ', '_')}" for name, value in inputs.items() if not value and name != "S4 runtime"]
    if len(run_ids) > 1:
        issues.append("artifact_run_id_mismatch")
    if inputs.get("S1", {}).get("stage") != "S1":
        issues.append("s1_not_usable")
    return issues


def _first_candidate(compare: dict[str, Any] | None) -> dict[str, Any] | None:
    candidates = (compare or {}).get("candidates") or []
    return candidates[0] if candidates else None


def _matching_candidate(validate: dict[str, Any] | None, candidate_id: str | None) -> dict[str, Any] | None:
    return next(
        (item for item in (validate or {}).get("validated_candidates") or [] if item.get("candidate_id") == candidate_id),
        None,
    )


def _candidate_summary(candidate: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "candidate_id": (candidate or {}).get("candidate_id"),
        "title": (candidate or {}).get("title") or "unknown",
        "source_url": (candidate or {}).get("source_url") or "unknown",
    }


def _merge_candidate_details(
    scan: dict[str, Any],
    compare: dict[str, Any] | None,
    selected: dict[str, Any] | None,
) -> dict[str, Any] | None:
    candidate_id = (selected or {}).get("candidate_id")
    merged: dict[str, Any] = {}
    for candidate in (
        _find_candidate(scan.get("candidates") or [], candidate_id),
        _find_candidate((compare or {}).get("candidates") or [], candidate_id),
        selected,
    ):
        if candidate:
            merged.update(candidate)
    return merged or selected


def _find_candidate(candidates: list[dict[str, Any]], candidate_id: Any) -> dict[str, Any] | None:
    if candidate_id:
        match = next((item for item in candidates if item.get("candidate_id") == candidate_id), None)
        if match:
            return match
    return candidates[0] if candidates else None


def _report_status(issues: list[str], runtime: dict[str, Any] | None) -> str:
    if issues:
        return "incomplete_artifacts"
    if runtime and runtime.get("status") == "cleanup_verified":
        if _is_abort_cleanup(runtime):
            return "final_without_console_review"
        if _runtime_requires_screenshot(runtime) and not _console_screenshot_count(runtime):
            return "incomplete_artifacts"
        if _runtime_requires_screenshot(runtime) and not _console_display_channel_confirmed(runtime):
            return "incomplete_artifacts"
        return "final"
    return "interim"


def _conclusion(candidate: dict[str, Any] | None, runtime: dict[str, Any] | None) -> dict[str, str]:
    if runtime and runtime.get("status") == "cleanup_verified":
        if _is_abort_cleanup(runtime):
            return {
                "status": "cleaned_without_console_review",
                "text": "PoC 已因成本控制完成受控 cleanup，但未完成 Infrastructure Composer 截圖人工確認；不能作為 actual-PoC final 結論。",
            }
        if _console_screenshot_count(runtime):
            return {
                "status": "validated_and_cleaned",
                "text": "實際 PoC 已通過自動化驗證與 Infrastructure Composer 截圖人工確認，cleanup 回查也已完成。",
            }
        return {
            "status": "cleanup_verified_missing_console_screenshot",
            "text": "cleanup 已完成，但新版 runtime 缺少 Infrastructure Composer 截圖人工確認 metadata；不能當成完整 actual-PoC final 結論。",
        }
    verification = (runtime or {}).get("verification") or {}
    if (runtime or {}).get("status") == "awaiting_console_review":
        if verification.get("cloudformation_reference_mode") == "verified" and verification.get("lambda_invoke") == "verified":
            return {"status": "poc_passed_pending_closure", "text": "PoC 技術驗證通過。CloudFormation deployment、REFERENCE 設定與 Lambda invoke 已通過。AWS Console review 與 cleanup 尚待完成。"}
        return {"status": "poc_passed_pending_closure", "text": "PoC 技術驗證已通過自動化檢查。AWS Console review 與 cleanup 尚待完成。"}
    if (runtime or {}).get("status") == "ready_for_cleanup":
        return {"status": "poc_passed_ready_for_cleanup", "text": "PoC 技術驗證與 AWS Console review 均已確認成功；待執行受控 cleanup。"}
    if candidate and _recommend_poc(candidate):
        return {
            "status": "poc_recommended_awaiting_approval",
            "text": "Skill 3 已完成 PoC 預估報價，建議進入實際 Skill 4 受控付費 PoC；仍須具名人員完成部署授權，且尚無 runtime 證據。",
        }
    return {"status": "unknown", "text": "尚無足夠的 Skill 3 或 Skill 4 證據形成 PoC 結論。"}


def _news_application_summary(candidate: dict[str, Any] | None) -> dict[str, str]:
    candidate = candidate or {}
    title = candidate.get("title") or "這項新功能"
    candidates = _source_summary_candidates(candidate)
    source_text = max(candidates, key=_application_summary_score) if candidates else ""
    if source_text:
        text = f"新聞指出：{_compact_sentence(_clean_source_summary(source_text))}"
    else:
        text = f"{title} 的應用面優勢尚未能從 S1/S2 來源摘錄中整理；目前只能保留來源與後續驗證問題。"
    return {
        "status": "source_backed" if source_text else "unknown",
        "text": text,
    }


def _source_summary_candidates(candidate: dict[str, Any]) -> list[str]:
    fetched = candidate.get("fetched_source") or {}
    dimensions = candidate.get("comparison_dimensions") or {}
    capability_excerpts = (
        (dimensions.get("source_backed_capabilities") or {}).get("excerpts")
        or (dimensions.get("source_backed_capabilities") or {}).get("source_excerpts")
        or []
    )
    values = [
        fetched.get("description"),
        *(candidate.get("initial_claims") or []),
        fetched.get("text_excerpt"),
        *capability_excerpts,
    ]
    return [str(value).strip() for value in values if str(value or "").strip()]


def _application_summary_score(value: str) -> int:
    text = value.lower()
    markers = [
        "支援",
        "優勢",
        "消除",
        "縮短",
        "改善",
        "直接",
        "無需",
        "高效能",
        "共享",
        "access",
        "accessible",
        "benefits",
        "eliminating",
        "latencies",
        "directly",
        "without",
        "faster",
    ]
    score = sum(3 for marker in markers if marker in text)
    if "透過以下方式了解" in value:
        score -= 6
    if len(value) > 80:
        score += 2
    return score


def _clean_source_summary(value: str) -> str:
    text = " ".join(str(value).split())
    text = text.replace("透過以下方式了解有關 AWS 新增功能的更多信息", "").strip()
    return text


def _evaluation_summary(candidate: dict[str, Any] | None) -> dict[str, Any]:
    candidate = candidate or {}
    dimensions = candidate.get("dimension_scores") or {}
    region = candidate.get("region_status") or {}
    score = candidate.get("weighted_score")
    score_text = f"{score} / 5" if score is not None else "未記錄 / 5"
    return {
        "weighted_score": candidate.get("weighted_score"),
        "confidence": candidate.get("confidence") or "unknown",
        "dimensions": dimensions,
        "rows": [
            ("Skill 3 加權分（滿分 5）", score_text),
            ("區域狀態", _display_status(region.get("status") or "unknown")),
            ("建議進入實際 Skill 4 PoC", _yes_no_unknown(_recommend_poc(candidate))),
            ("成本", _display_status((candidate.get("cost_estimate") or {}).get("status") or "unknown")),
        ],
    }


def _cost_quote(candidate: dict[str, Any] | None) -> dict[str, Any]:
    estimate = (candidate or {}).get("cost_estimate") or {}
    quote = estimate.get("quote") or {}
    if quote:
        return quote
    return {
        "status": estimate.get("status") or "unknown",
        "quote_id": estimate.get("quote_id"),
        "currency": "USD",
        "expected_total_usd": estimate.get("estimated_usd"),
        "estimated_range_usd": estimate.get("range_usd") or {},
        "scenarios": {},
        "disclaimer": "成本報價資料未記錄在 Skill 3 artifact。",
        "sources": [],
    }


def _cost_reconciliation(candidate: dict[str, Any] | None, billing: dict[str, Any] | None) -> dict[str, Any]:
    quote = _cost_quote(candidate)
    expected = quote.get("expected_total_usd")
    actual = _actual_billing_cost(billing)
    status = "pending_actual_cost"
    delta = None
    if actual["status"] == "attributed" and isinstance(expected, (int, float)):
        delta = round(float(actual["amount_usd"]) - float(expected), 6)
        status = "compared"
    elif actual["status"] == "attributed":
        status = "actual_available_without_estimate"
    return {
        "schema_version": "poc.cost-reconciliation.v1",
        "status": status,
        "estimated": {
            "status": quote.get("status") or "unknown",
            "quote_id": quote.get("quote_id"),
            "expected_total_usd": expected,
            "range_usd": quote.get("estimated_range_usd") or {},
            "currency": quote.get("currency") or "USD",
            "source": "Skill 3 public list-price quote" if quote.get("status") == "estimated" else "not_available",
        },
        "actual": actual,
        "delta_usd": delta,
        "rule": "Actual cost is shown only when an attributable AWS Billing, Cost Explorer, or CUR artifact records it; runtime duration is not converted into actual cost.",
    }


def _actual_billing_cost(billing: dict[str, Any] | None) -> dict[str, Any]:
    if not billing:
        return _pending_actual_cost("No attributable AWS Billing, Cost Explorer, or CUR artifact was provided.")

    payload = billing.get("actual_cost") if isinstance(billing.get("actual_cost"), dict) else billing
    amount = (
        payload.get("amount_usd")
        if payload.get("amount_usd") is not None
        else payload.get("total_usd")
    )
    source_type = str(payload.get("source_type") or payload.get("source") or "").lower()
    attribution = str(
        payload.get("attribution_status")
        or payload.get("attribution")
        or payload.get("status")
        or ""
    ).lower()
    is_attributed = payload.get("attributable") is True or attribution in {"attributed", "attributable", "final"}
    is_billing_source = source_type in {"cost_explorer", "aws_cost_explorer", "billing", "aws_billing", "cur", "aws_cur"}
    if not isinstance(amount, (int, float)) or not is_attributed or not is_billing_source:
        return _pending_actual_cost(
            "Billing artifact is present, but it does not prove an attributable actual AWS cost."
        )

    return {
        "status": "attributed",
        "amount_usd": round(float(amount), 6),
        "currency": payload.get("currency") or "USD",
        "source_type": payload.get("source_type") or payload.get("source"),
        "source_artifact": payload.get("source_artifact") or billing.get("source_artifact"),
        "period_start": payload.get("period_start"),
        "period_end": payload.get("period_end"),
        "attribution_key": payload.get("attribution_key"),
        "note": payload.get("note"),
    }


def _pending_actual_cost(reason: str) -> dict[str, Any]:
    return {
        "status": "pending",
        "amount_usd": None,
        "currency": "USD",
        "source_type": "not_available",
        "source_artifact": None,
        "reason": reason,
    }


def _render_cost_quote(quote: dict[str, Any]) -> list[str]:
    lines = ["", "## PoC 成本估算報價單", ""]
    if quote.get("status") != "estimated":
        lines.extend(
            [
                f"- 報價狀態：{_display_status(quote.get('status') or 'unknown')}",
                f"- Quote ID：{quote.get('quote_id') or 'unknown'}",
                "- 結果：目前沒有已登錄且可稽核的費率模型，不填造金額。",
            ]
        )
        return lines

    expected = (quote.get("scenarios") or {}).get("expected") or {}
    price_range = quote.get("estimated_range_usd") or {}
    assumptions = expected.get("assumptions") or {}
    lines.extend(
        [
            f"- Quote ID：{quote.get('quote_id')}",
            f"- 區域：{quote.get('target_region')}",
            f"- 幣別：{quote.get('currency')}",
            f"- 價格快照：{quote.get('price_snapshot_date')}",
            f"- 有效期限：{quote.get('valid_until')}",
            (
                f"- 情境總額：低 **${_format_money(price_range.get('low'))}**／"
                f"預期 **${_format_money(price_range.get('expected'))}**／"
                f"高 **${_format_money(price_range.get('high'))}**"
            ),
            f"- 建議核准上限：**${_format_money(quote.get('recommended_approval_ceiling_usd'))}**",
            f"- 報價性質：{_display_status(quote.get('quote_kind') or 'non_binding_public_price_estimate')}；即時 Pricing API：{_yes_no_unknown(quote.get('live_pricing_api_used'))}",
            f"- 計價口徑：{_quote_billing_basis_note(expected)}",
            f"- 預期情境假設：{_format_quote_assumptions(assumptions)}。",
            f"- 人工需確認的 PoC 資源：{_quote_resource_scope(expected)}。",
            f"- 主要成本驅動：{_quote_cost_driver(expected)}",
            "",
            "### 預期情境明細",
            "",
            "| 項目 | 費率 | 用量 | 小計 USD |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for item in expected.get("line_items") or []:
        lines.append(
            f"| {item.get('item')} | {_format_number(item.get('rate_usd'))} {item.get('rate_unit')} | "
            f"{_format_number(item.get('quantity'))} {item.get('quantity_unit')} | "
            f"{_format_money(item.get('subtotal_usd'))} |"
        )
    lines.extend(
        [
            f"| **預期總額** |  |  | **{_format_money(expected.get('total_usd'))}** |",
        ]
    )
    lines.extend(["", "### 官方價格來源", ""])
    lines.extend(
        f"- [{source.get('purpose')}]({source.get('url')})"
        for source in quote.get("sources") or []
    )
    return lines


def _format_quote_assumptions(assumptions: dict[str, Any]) -> str:
    if "active_gb" in assumptions:
        return f"{assumptions.get('hours')} 小時、{assumptions.get('active_gb')} GB active storage"
    if "artifact_gb" in assumptions:
        return (
            f"{assumptions.get('hours')} 小時、{assumptions.get('artifact_gb')} GB artifact、"
            f"{assumptions.get('lambda_requests')} 次 Lambda request、"
            f"{assumptions.get('lambda_gb_seconds')} GB-seconds"
        )
    return "詳見情境明細"


def _quote_billing_basis_note(expected: dict[str, Any]) -> str:
    line_items = expected.get("line_items") or []
    units = {str(item.get("rate_unit") or "").lower() for item in line_items}
    notes: list[str] = []
    if any("month" in unit for unit in units):
        notes.append("月費型資源以每月價格為基礎，再依 PoC 使用時數折算")
    if any("instance-hour" in unit for unit in units):
        notes.append("EC2 等運算資源依啟用小時計算")
    if any(str(item.get("rate_key") or "").startswith("lambda_") for item in line_items):
        notes.append("Lambda 只有被呼叫時才計請求數與執行時間/記憶體用量")
    if any("/request" in unit or "request" in unit for unit in units):
        notes.append("請求型項目依實際請求量增加")
    return "；".join(notes) if notes else "依預期情境明細中的用量與公開牌價計算"


def _quote_resource_scope(expected: dict[str, Any]) -> str:
    names = [str(item.get("item") or "").strip() for item in expected.get("line_items") or [] if item.get("item")]
    if not names:
        return "未記錄"
    return "、".join(_dedupe(names)[:8])


def _quote_cost_driver(expected: dict[str, Any]) -> str:
    line_items = [
        item
        for item in expected.get("line_items") or []
        if isinstance(item.get("subtotal_usd"), (int, float))
    ]
    if not line_items:
        return "未記錄。"
    highest = max(line_items, key=lambda item: float(item.get("subtotal_usd") or 0))
    return (
        f"預期情境中最高的是 {highest.get('item')}（USD {_format_money(highest.get('subtotal_usd'))}）；"
        f"當 {highest.get('formula') or '對應用量'} 增加時，這項費用會上升。"
    )


def _render_cost_reconciliation(reconciliation: dict[str, Any]) -> list[str]:
    estimated = reconciliation.get("estimated") or {}
    actual = reconciliation.get("actual") or {}
    lines = [
        "",
        "## 預估成本 vs 可歸因實際帳務成本",
        "",
        "| 項目 | 狀態 | 金額 USD | 證據 |",
        "| --- | --- | ---: | --- |",
        (
            f"| Skill 3 公開牌價估算 | {_display_status(estimated.get('status') or 'unknown')} | "
            f"{_format_money(estimated.get('expected_total_usd'))} | "
            f"{estimated.get('quote_id') or estimated.get('source') or 'unknown'} |"
        ),
    ]
    actual_source = _display_status(actual.get("source_artifact") or actual.get("source_type") or "not_available")
    lines.append(
        f"| 可歸因實際帳務成本 | {_display_status(actual.get('status') or 'unknown')} | "
        f"{_format_money(actual.get('amount_usd'))} | {actual_source} |"
    )
    lines.append(
        f"| 差異（實際 - 預估） | {_display_status(reconciliation.get('status') or 'unknown')} | "
        f"{_format_money(reconciliation.get('delta_usd'))} | {reconciliation.get('rule')} |"
    )
    if actual.get("status") == "pending":
        lines.extend(["", f"- 實際成本狀態：{_display_status('pending')}。{actual.get('reason')}"])
        lines.append("- 不以 EC2 執行時間、CloudFormation 狀態或 runtime artifact 推算實際 AWS 帳務成本。")
    return lines


def _pre_cleanup_usage_snapshot(runtime: dict[str, Any] | None) -> dict[str, Any]:
    snapshot = (runtime or {}).get("pre_cleanup_usage_snapshot")
    if isinstance(snapshot, dict):
        return snapshot
    return {
        "schema_version": "s4.pre-cleanup-usage-snapshot.v1",
        "status": "not_recorded",
        "billing_evidence": False,
        "actual_cost_status": "not_billing_evidence",
        "sections": {},
        "rule": "cleanup 前未提供即時用量快照；實際成本仍只能由 Billing、Cost Explorer 或 CUR artifact 證明。",
    }


def _usage_snapshot_status_label(value: Any) -> str:
    labels = {
        "captured": "已擷取",
        "partial": "部分擷取",
        "unavailable": "無法擷取",
        "not_recorded": "未記錄",
        "not_billing_evidence": "非帳務證據",
        "unknown": "未知",
    }
    return labels.get(str(value or "unknown"), str(value or "未知"))


def _render_pre_cleanup_usage_snapshot(snapshot: dict[str, Any]) -> list[str]:
    lines = ["", "## cleanup 前即時用量快照", ""]
    if snapshot.get("status") == "not_recorded":
        lines.extend(
            [
                "- 狀態：未記錄。",
                "- 說明：這不影響 cleanup 結論，但 Skill 5 無法列出刪除前的即時用量證據。",
            ]
        )
        return lines

    sections = snapshot.get("sections") or {}
    timeline = snapshot.get("timeline") or {}
    elapsed = timeline.get("elapsed_seconds")
    elapsed_text = f"{round(float(elapsed) / 60, 2)} 分鐘" if isinstance(elapsed, (int, float)) else "未記錄"
    lines.extend(
        [
            f"- 快照狀態：{_usage_snapshot_status_label(snapshot.get('status') or 'unknown')}",
            f"- 擷取時間：{snapshot.get('captured_at') or 'unknown'}",
            f"- 建立到 cleanup 前經過：約 {elapsed_text}",
            "- 性質：這是 runtime facts，不是 AWS 帳單；實際成本仍需 Billing、Cost Explorer 或 CUR artifact。",
            "",
            "| 類別 | cleanup 前看到的證據 |",
            "| --- | --- |",
        ]
    )
    cloudformation = sections.get("cloudformation") or {}
    if cloudformation:
        tags = cloudformation.get("tags") or {}
        lines.append(
            f"| CloudFormation | 狀態 {cloudformation.get('stack_status') or 'unknown'}；"
            f"資源數 {cloudformation.get('resource_count') if cloudformation.get('resource_count') is not None else 'unknown'}；"
            f"tags {len(tags) if isinstance(tags, dict) else 'unknown'} |"
        )
    s3 = sections.get("s3") or {}
    if s3:
        s3_tags = (s3.get("tags") or {}).get("values") if isinstance(s3.get("tags"), dict) else {}
        lines.append(
            f"| S3 | current objects {s3.get('object_count_current', 'unknown')}；"
            f"versions {s3.get('object_version_count', 'unknown')}；"
            f"delete markers {s3.get('delete_marker_count', 'unknown')}；"
            f"size bytes {s3.get('total_size_bytes', 'unknown')}；"
            f"tags {len(s3_tags) if isinstance(s3_tags, dict) else 'unknown'} |"
        )
    lambda_section = sections.get("lambda") or {}
    if lambda_section:
        metrics = lambda_section.get("cloudwatch_metrics") or {}
        invocations = (metrics.get("Invocations") or {}).get("sum")
        errors = (metrics.get("Errors") or {}).get("sum")
        lambda_tags = (lambda_section.get("tags") or {}).get("values") if isinstance(lambda_section.get("tags"), dict) else {}
        lines.append(
            f"| Lambda | runtime {lambda_section.get('runtime') or 'unknown'}；"
            f"code size {lambda_section.get('code_size_bytes', 'unknown')} bytes；"
            f"invocations {invocations if invocations is not None else 'no datapoints'}；"
            f"errors {errors if errors is not None else 'no datapoints'}；"
            f"tags {len(lambda_tags) if isinstance(lambda_tags, dict) else 'unknown'} |"
        )
    ec2 = sections.get("ec2") or {}
    if ec2:
        ec2_tags = ec2.get("tags") or {}
        lines.append(
            f"| EC2 | instance {ec2.get('instance_id') or 'unknown'}；"
            f"state {ec2.get('state') or ec2.get('status') or 'unknown'}；"
            f"type {ec2.get('instance_type') or 'unknown'}；"
            f"tags {len(ec2_tags) if isinstance(ec2_tags, dict) else 'unknown'} |"
        )
    for error in snapshot.get("collection_errors") or []:
        lines.append(f"| 蒐集限制 | {error} |")
    if len(lines) == 10:
        lines.append("| 無可列資料 | snapshot 存在，但沒有可呈現的 resource section。 |")
    return lines


def _validation_summary(validation: dict[str, Any] | None, runtime: dict[str, Any] | None) -> dict[str, Any]:
    runtime = runtime or {}
    verification = runtime.get("verification") or {}
    cleanup = runtime.get("cleanup") or {}
    return {
        "rows": [
            ("Skill 4 validation", _display_status((validation or {}).get("validation_status") or "unknown")),
            ("CloudFormation", _display_status((runtime.get("deployment") or {}).get("stack_status") or "unknown")),
            ("自動化驗證", _verification_status(verification)),
            ("AWS Console review", _display_status((runtime.get("console_review") or {}).get("status") or "unknown")),
            ("Console 截圖證據", _console_screenshot_status(runtime)),
            ("cleanup", _display_status(cleanup.get("status") or (validation or {}).get("cleanup_status") or "unknown")),
        ]
    }


def _verification_status(verification: dict[str, Any]) -> str:
    known = [
        value
        for key, value in verification.items()
        if key not in {"success_criteria", "recipe"} and isinstance(value, str)
    ]
    if known and all(value == "verified" for value in known):
        return _display_status("verified")
    return ", ".join(_display_status(value) for value in known) if known else _display_status("unknown")


def _verified_facts(
    scan: dict[str, Any],
    compare: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
    billing: dict[str, Any] | None,
) -> list[str]:
    facts: list[str] = []
    if candidate and candidate.get("source_url"):
        facts.append(f"官方來源已記錄：{candidate['source_url']}")
    if (candidate or {}).get("weighted_score") is not None:
        facts.append(f"Skill 3 加權分已依固定 rubric 計算：{candidate['weighted_score']}")
    quote = ((candidate or {}).get("cost_estimate") or {}).get("quote") or {}
    if quote.get("status") == "estimated":
        facts.append(
            f"PoC 成本估算報價單已建立：{quote.get('quote_id')}，"
            f"預期 USD {quote.get('expected_total_usd')}。"
        )
    actual = _actual_billing_cost(billing)
    if actual.get("status") == "attributed":
        facts.append(
            f"可歸因實際帳務成本已由 {actual.get('source_type')} 記錄："
            f"USD {actual.get('amount_usd')}。"
        )
    if (runtime or {}).get("deployment", {}).get("stack_status") == "CREATE_COMPLETE":
        facts.append("CloudFormation stack 已達 CREATE_COMPLETE。")
    screenshot_count = _console_screenshot_count(runtime)
    if screenshot_count:
        facts.append(f"AWS Console review 已以 {screenshot_count} 張截圖透過 GUI 或對話交由具名人員確認。")
    usage_snapshot = _pre_cleanup_usage_snapshot(runtime)
    if usage_snapshot.get("status") in {"captured", "partial"}:
        facts.append(
            f"cleanup 前即時用量快照已記錄：{_usage_snapshot_status_label(usage_snapshot.get('status'))}；"
            "這是 runtime facts，不是 AWS 帳單。"
        )
    for key, value in ((runtime or {}).get("verification") or {}).items():
        if key != "success_criteria" and value == "verified":
            facts.append(f"Skill 4 自動化驗證已通過：{key}。")
    return facts


def _unknowns(
    compare: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
    validation: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
    billing: dict[str, Any] | None,
) -> list[str]:
    items = list(((candidate or {}).get("evidence_refs") or {}).get("evidence_limits") or [])
    if ((candidate or {}).get("cost_estimate") or {}).get("status") != "estimated":
        items.append("官方定價或實際成本尚未在 artifact 中證實。")
    elif not runtime:
        items.append("報價單是公開牌價估算；實際 AWS 費用需在部署後以帳務資料核對。")
    if _actual_billing_cost(billing).get("status") != "attributed":
        items.append("可歸因實際帳務成本尚未由 Cost Explorer、Billing 或 CUR artifact 證實；不得以 runtime 估算代替。")
    if (runtime or {}).get("console_review", {}).get("status") != "confirmed":
        items.append("AWS Console review 尚未完成或尚未記錄。")
    elif (runtime or {}).get("schema_version") == "s4.runtime-evidence.v3" and not _console_screenshot_count(runtime):
        items.append("此 PoC runtime 尚未記錄 Infrastructure Composer 截圖證據。")
    if _recommend_poc(candidate or {}):
        items.append("Skill 3 的 PoC 判斷只代表公開技術證據與成本/recipe 條件達標；公司工作負載適配性未評估。")
    if (runtime or {}).get("cleanup", {}).get("status") != "verified":
        items.append("cleanup 尚未完成或尚未記錄。")
    return _dedupe(items)


def _next_reminders(candidate: dict[str, Any] | None, runtime: dict[str, Any] | None) -> list[str]:
    reminders = list((candidate or {}).get("stop_conditions") or [])
    if (runtime or {}).get("status") == "awaiting_console_review":
        reminders.append("截取 Infrastructure Composer 畫面、在 GUI 或對話中交由人類確認後，才能執行受控 cleanup。")
    return _dedupe(reminders)


def _future_work(
    candidate: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
    billing: dict[str, Any] | None,
) -> list[str]:
    items: list[str] = []
    if _actual_billing_cost(billing).get("status") != "attributed":
        items.append("補上可歸因的 Cost Explorer、Billing 或 CUR artifact，讓 Skill 5 能比較預估成本與實際帳務成本。")
    if runtime and runtime.get("status") == "cleanup_verified":
        items.append("用同一篇新聞的應用面優勢設計第二輪 PoC 問題，例如增加資料量、併發、錯誤情境或觀測指標，而不是只證明資源能建立。")
    elif runtime and runtime.get("status") == "awaiting_console_review":
        items.append("完成 Infrastructure Composer 人工確認、Skill 5 證據審閱與受控 cleanup，再將報告升級為 final。")
    elif _recommend_poc(candidate or {}):
        items.append("在進入 Skill 4 前，由人類確認 PoC 會使用的 AWS 資源、預期用量、成本上限、成功條件與 cleanup 範圍。")
    else:
        items.append("先補齊缺少的官方證據、用量範圍或 deployable recipe，再判斷是否值得進入 PoC。")
    items.append("把這個候選對應到一個明確的人類工作場景，補上目前做法、痛點、量測指標與導入後預期改善。")
    items.append("整理成 final proposal / 論文可引用的案例：問題、方法、證據鏈、限制、價值與下一步。")
    return _dedupe(items)


def _reviewer_questions(
    candidate: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
    billing: dict[str, Any] | None,
) -> list[str]:
    quote = _cost_quote(candidate)
    expected = (quote.get("scenarios") or {}).get("expected") or {}
    driver = _quote_cost_driver(expected).rstrip("。")
    questions = [
        "這篇新聞提到的新功能，最適合改善哪一個真實使用者流程？現有流程的 baseline 是什麼？",
        "Skill 1 到 Skill 5 的每個結論分別由哪個 artifact 支撐？哪些只是推論或待驗證？",
        f"報價單中哪一項最貴？{driver}；什麼實際使用情境會讓它增加？",
        "PoC 會建立哪些 AWS 資源？人類是否已確認這些資源、Region、成本上限與 cleanup 範圍？",
        "這次 PoC 只驗證功能可行，還是也驗證效能、可靠性、權限治理與可維運性？",
    ]
    if _actual_billing_cost(billing).get("status") != "attributed":
        questions.append("實際成本何時能用 Cost Explorer、Billing 或 CUR 歸因到這個 run？若不能歸因，報告要如何標示限制？")
    if not runtime:
        questions.append("尚未有 Skill 4 runtime 時，為什麼仍值得進入 PoC？部署前最小成功條件是什麼？")
    elif runtime.get("status") != "cleanup_verified":
        questions.append("目前還不能 cleanup 或 final 的阻塞點是 Console review、Skill 5 證據審閱，還是其他人工決策？")
    return _dedupe(questions)


def _related_topics(
    report_candidate: dict[str, Any] | None,
    compare: dict[str, Any] | None,
    selected: dict[str, Any] | None,
) -> list[str]:
    topics: list[str] = []
    for source in (report_candidate or {}, selected or {}):
        topics.extend(str(item) for item in source.get("related_aws_services") or [])
        topics.extend(str(item) for item in source.get("tags") or [])
    scope = (((selected or {}).get("comparison_dimensions") or {}).get("technology_scope") or {})
    topics.extend(str(item) for item in scope.get("services_detected") or [])
    topics.extend(["AWS Pricing Calculator", "Cost Explorer", "CloudFormation", "PoC cleanup", "Future work"])
    return _dedupe([_topic_label(item) for item in topics if item])


def _stage_evidence(
    scan: dict[str, Any],
    compare: dict[str, Any] | None,
    evaluate: dict[str, Any] | None,
    validate: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
    billing: dict[str, Any] | None,
    selected: dict[str, Any] | None,
    report_status: str,
) -> list[dict[str, str]]:
    candidate_id = (selected or {}).get("candidate_id")
    s2_candidate = _find_candidate((compare or {}).get("candidates") or [], candidate_id)
    quote = _cost_quote(selected)
    validation = _matching_candidate(validate, candidate_id)
    usage_snapshot = _pre_cleanup_usage_snapshot(runtime)
    actual = _actual_billing_cost(billing)
    rows = [
        {
            "stage": "S1 Scan",
            "status": scan.get("status") or "unknown",
            "evidence": (
                f"candidate_count={len(scan.get('candidates') or [])}；"
                f"external_fetch={_yes_no_unknown(scan.get('external_fetch_performed'))}；"
                f"source={_candidate_summary(_find_candidate(scan.get('candidates') or [], candidate_id))['source_url']}"
            ),
        },
        {
            "stage": "S2 Compare",
            "status": (compare or {}).get("status") or "unknown",
            "evidence": (
                f"candidate_count={len((compare or {}).get('candidates') or [])}；"
                f"linked_evidence={len(((s2_candidate or {}).get('linked_evidence') or {}).get('linked_sources') or [])}；"
                f"region={_display_status((((s2_candidate or {}).get('comparison_dimensions') or {}).get('target_region_eligibility') or {}).get('status') or 'unknown')}"
            ),
        },
        {
            "stage": "S3 Evaluate",
            "status": (evaluate or {}).get("status") or "unknown",
            "evidence": (
                f"score={selected.get('weighted_score') if selected else 'unknown'} / 5；"
                f"quote={quote.get('quote_id') or 'unknown'}；"
                f"recommend_poc={_yes_no_unknown(_recommend_poc(selected or {}))}"
            ),
        },
        {
            "stage": "S4 Validate",
            "status": (validation or {}).get("validation_status") or (runtime or {}).get("status") or "unknown",
            "evidence": (
                f"runtime={_display_status((runtime or {}).get('status') or 'unknown')}；"
                f"cloudformation={_display_status(((runtime or {}).get('deployment') or {}).get('stack_status') or 'unknown')}；"
                f"checks={_verification_status((runtime or {}).get('verification') or {})}"
            ),
        },
        {
            "stage": "S4 Cleanup",
            "status": ((runtime or {}).get("cleanup") or {}).get("status") or "unknown",
            "evidence": (
                f"cleanup={_display_status(((runtime or {}).get('cleanup') or {}).get('status') or 'unknown')}；"
                f"usage_snapshot={_usage_snapshot_status_label(usage_snapshot.get('status'))}"
            ),
        },
        {
            "stage": "S5 Report",
            "status": report_status,
            "evidence": (
                f"report_type={_display_status('final' if report_status == 'final' else 'interim')}；"
                f"actual_cost={_display_status(actual.get('status') or 'unknown')}"
            ),
        },
    ]
    return rows


def _funnel(scan: dict[str, Any], compare: dict[str, Any] | None, evaluate: dict[str, Any] | None, validate: dict[str, Any] | None) -> dict[str, int]:
    candidates = (compare or {}).get("candidates") or []
    return {
        "s1_candidates": len(scan.get("candidates") or []),
        "s2_candidates": len(candidates),
        "s2_region_verified": sum(1 for item in candidates if ((item.get("comparison_dimensions") or {}).get("target_region_eligibility") or {}).get("status") == "available_ap_southeast_1"),
        "s3_evaluated": len((evaluate or {}).get("evaluated_candidates") or []),
        "s4_validated": len((validate or {}).get("validated_candidates") or []),
    }


def _evidence_ledger(
    scan: dict[str, Any],
    compare: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
    billing: dict[str, Any] | None,
) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    source_url = (candidate or {}).get("source_url") or "unknown"
    if source_url != "unknown":
        entries.append({"claim": "候選技術的公開來源", "type": "source-backed fact", "status": "recorded", "source": source_url})
    for key, value in ((runtime or {}).get("verification") or {}).items():
        if key != "success_criteria":
            entries.append({"claim": key, "type": "runtime evidence", "status": str(value), "source": "S4 runtime artifact"})
    screenshot_count = _console_screenshot_count(runtime)
    if screenshot_count:
        entries.append(
            {
                "claim": "Infrastructure Composer Console review",
                "type": "human-reviewed screenshot evidence",
                "status": "confirmed",
                "source": f"S4 Console review evidence ({screenshot_count} screenshot metadata records)",
            }
        )
    quote = ((candidate or {}).get("cost_estimate") or {}).get("quote") or {}
    if quote.get("status") == "estimated":
        entries.append(
            {
                "claim": "PoC 成本估算",
                "type": "public list-price estimate",
                "status": "estimated",
                "source": str(quote.get("quote_id") or "Skill 3 cost quote"),
            }
        )
    actual = _actual_billing_cost(billing)
    if actual.get("status") == "attributed":
        entries.append(
            {
                "claim": "PoC 可歸因實際帳務成本",
                "type": "AWS billing evidence",
                "status": "attributed",
                "source": str(actual.get("source_artifact") or actual.get("source_type") or "billing artifact"),
            }
        )
    if not entries:
        entries.append({"claim": "尚無可呈現的證據帳本項目", "type": "unknown", "status": "unknown", "source": "artifact data gap"})
    return entries


def _yes_no_unknown(value: Any) -> str:
    if value is True:
        return "是"
    if value is False:
        return "否"
    return "未記錄"


def _display_status(value: Any) -> str:
    text = str(value or "unknown")
    labels = {
        "actual_available_without_estimate": "已有實際成本但缺少預估基準",
        "attributed": "已歸因",
        "awaiting_console_review": "等待 Console 人工確認",
        "awaiting_poc_approval": "等待 PoC 授權",
        "captured_and_confirmed": "已截圖並經人類確認",
        "captured_channel_unconfirmed": "已截圖但尚未確認顯示管道",
        "cleanup_verified": "清除已驗證",
        "closed_without_console_review": "已關閉但未完成 Console 確認",
        "compared": "已完成比較",
        "confirmed": "已確認",
        "CREATE_COMPLETE": "CloudFormation 建立完成",
        "estimated": "已完成估算",
        "final": "最終報告",
        "interim": "階段性報告",
        "medium": "中等",
        "high": "高",
        "low": "低",
        "incomplete": "估價資料不足",
        "needs_registered_cost_model": "缺少已註冊成本模型",
        "non_binding_public_price_estimate": "非正式公開牌價估算",
        "not_applicable_no_cloud_resources_created": "不適用，未建立雲端資源",
        "not_available": "無可用資料",
        "not_recorded": "未記錄",
        "not_recommended_for_poc": "不建議進入實際 PoC",
        "pending": "待補實際帳務證據",
        "pending_actual_cost": "待補實際成本",
        "poc_ready_for_manual_start": "PoC 可由人類授權啟動",
        "region_unknown": "區域支援尚未確認",
        "available_ap_southeast_1": "新加坡區域可用",
        "unknown": "未記錄",
        "verified": "已驗證",
    }
    return labels.get(text, text)


def _console_screenshot_count(runtime: dict[str, Any] | None) -> int:
    evidence = ((runtime or {}).get("console_review") or {}).get("evidence") or {}
    screenshots = evidence.get("screenshots") if isinstance(evidence, dict) else None
    return len(screenshots) if isinstance(screenshots, list) else 0


def _console_display_channel_confirmed(runtime: dict[str, Any] | None) -> bool:
    return ((runtime or {}).get("console_review") or {}).get("display_channel_confirmed") in {"gui", "conversation"}


def _is_abort_cleanup(runtime: dict[str, Any] | None) -> bool:
    cleanup = (runtime or {}).get("cleanup") or {}
    review = (runtime or {}).get("console_review") or {}
    return cleanup.get("cleanup_mode") == "abort_without_console_review" or review.get("status") == "skipped_for_cost_control"


def _runtime_requires_screenshot(runtime: dict[str, Any] | None) -> bool:
    return (runtime or {}).get("schema_version") == "s4.runtime-evidence.v3"


def _console_screenshot_status(runtime: dict[str, Any] | None) -> str:
    count = _console_screenshot_count(runtime)
    if count:
        if _console_display_channel_confirmed(runtime):
            return f"已截圖並經人類確認（{count} 張）"
        return f"已截圖但尚未確認顯示管道（{count} 張）"
    return _display_status(((runtime or {}).get("console_review") or {}).get("evidence_status") or "not_recorded")


def _recommend_poc(candidate: dict[str, Any]) -> bool:
    if "recommend_poc" in candidate:
        return bool(candidate.get("recommend_poc"))
    if "eligible_for_poc_review" in candidate:
        return bool(candidate.get("eligible_for_poc_review"))
    if "eligible_for_paid_poc_review" in candidate:
        return bool(candidate.get("eligible_for_paid_poc_review"))
    return bool(candidate.get("recommend_s4"))


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value).strip()))


def _compact_sentence(value: str, limit: int = 260) -> str:
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    clipped = text[: limit - 1].rstrip()
    sentence_end = max(clipped.rfind(mark) for mark in ("。", "！", "？", ".", "!", "?"))
    if sentence_end >= 80:
        clipped = clipped[: sentence_end + 1]
    else:
        space = clipped.rfind(" ")
        if space >= 80:
            clipped = clipped[:space]
    return clipped.rstrip() + "…"


def _topic_label(value: str) -> str:
    cleaned = str(value).strip().replace("_", " ")
    return " ".join(part for part in cleaned.split() if part)


def _format_number(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return str(value if value is not None else "未記錄")
    return f"{float(value):.9f}".rstrip("0").rstrip(".")


def _format_money(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return str(value if value is not None else "未記錄")
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    if "." not in text:
        return text + ".00"
    decimals = len(text.split(".", 1)[1])
    return text + ("0" * max(0, 2 - decimals))
