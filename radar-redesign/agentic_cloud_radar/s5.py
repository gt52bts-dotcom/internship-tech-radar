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
    run_id = str(scan.get("run_id") or "unknown-run")
    evaluated = list((evaluate or {}).get("evaluated_candidates") or [])
    selected = evaluated[0] if evaluated else _first_candidate(compare)
    validation = _matching_candidate(validate, selected.get("candidate_id") if selected else None)
    report = {
        "schema_version": "s5.report.v1",
        "stage": "S5",
        "run_id": run_id,
        "reported_at": datetime.now(timezone.utc).isoformat(),
        "status": _report_status(issues, runtime),
        "report_type": "final" if (runtime or {}).get("status") == "cleanup_verified" else "interim",
        "input_contract": {
            "rule": "Only S1, S2, S3, and S4 artifacts may support report claims; missing evidence is unknown.",
            "stages_received": [name for name, artifact in inputs.items() if artifact],
        },
        "input_issues": issues,
        "candidate": _candidate_summary(selected),
        "conclusion": _conclusion(selected, runtime),
        "evaluation": _evaluation_summary(selected),
        "cost_quote": _cost_quote(selected),
        "cost_reconciliation": _cost_reconciliation(selected, billing),
        "validation": _validation_summary(validation, runtime),
        "verified_facts": _verified_facts(scan, compare, selected, runtime, billing),
        "unknown_or_not_verified": _unknowns(compare, selected, validation, runtime, billing),
        "next_reminders": _next_reminders(selected, runtime),
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
        f"- 報告狀態：{report['report_type']}",
        f"- Run ID：{report['run_id']}",
        f"- 來源：{candidate['source_url'] or 'unknown'}",
        "",
        "## 一句結論",
        "",
        f"> {report['conclusion']['text']}",
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
    lines.extend(["", "## 技術驗證", "", "| 檢查 | 狀態 |", "| --- | --- |"])
    for label, value in report["validation"]["rows"]:
        lines.append(f"| {label} | {value} |")
    lines.extend(["", "## 已證實的事實", ""])
    lines.extend(f"- {item}" for item in report["verified_facts"] or ["unknown"])
    lines.extend(["", "## 尚未驗證或證據不足", ""])
    lines.extend(f"- {item}" for item in report["unknown_or_not_verified"] or ["unknown"])
    lines.extend(["", "## 後續提醒", ""])
    lines.extend(f"- {item}" for item in report["next_reminders"] or ["無額外提醒"])
    lines.extend(["", "## 證據帳本", "", "| 敘述 | 類型 | 狀態 | 證據 |", "| --- | --- | --- | --- |"])
    for entry in report["evidence_ledger"]:
        lines.append(f"| {entry['claim']} | {entry['type']} | {entry['status']} | {entry['source']} |")
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
            "conclusion": report["conclusion"],
        },
        "score": {
            "weighted_score": report["evaluation"].get("weighted_score"),
            "confidence": report["evaluation"].get("confidence"),
            "dimensions": dimensions,
        },
        "cost_quote": report["cost_quote"],
        "cost_reconciliation": report["cost_reconciliation"],
        "validation_checks": checks,
        "verified_facts": report["verified_facts"],
        "unknown_or_not_verified": report["unknown_or_not_verified"],
        "next_reminders": report["next_reminders"],
        "evidence_ledger": report["evidence_ledger"],
        "funnel": report["funnel"],
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


def _report_status(issues: list[str], runtime: dict[str, Any] | None) -> str:
    if issues:
        return "incomplete_artifacts"
    if runtime and runtime.get("status") == "cleanup_verified":
        return "final"
    return "interim"


def _conclusion(candidate: dict[str, Any] | None, runtime: dict[str, Any] | None) -> dict[str, str]:
    if runtime and runtime.get("status") == "cleanup_verified":
        return {"status": "validated_and_cleaned", "text": "PoC 技術驗證通過，且 cleanup 已完成。"}
    verification = (runtime or {}).get("verification") or {}
    if (runtime or {}).get("status") == "awaiting_console_review":
        if verification.get("cloudformation_reference_mode") == "verified" and verification.get("lambda_invoke") == "verified":
            return {"status": "poc_passed_pending_closure", "text": "PoC 技術驗證通過。CloudFormation deployment、REFERENCE 設定與 Lambda invoke 已通過。AWS Console review 與 cleanup 尚待完成。"}
        return {"status": "poc_passed_pending_closure", "text": "PoC 技術驗證已通過自動化檢查。AWS Console review 與 cleanup 尚待完成。"}
    if candidate and _recommend_low_risk_validation(candidate):
        if _eligible_for_poc_review(candidate):
            return {
                "status": "low_risk_and_poc_review_recommended",
                "text": "Skill 3 建議進入低風險 Skill 4 驗證，且公開證據已達 PoC 審查門檻；尚無完整 PoC runtime 證據。",
            }
        return {
            "status": "low_risk_validation_recommended",
            "text": "Skill 3 建議進入低風險 Skill 4 驗證；公開證據尚未達 PoC 審查門檻。",
        }
    return {"status": "unknown", "text": "尚無足夠的 Skill 3 或 Skill 4 證據形成 PoC 結論。"}


def _evaluation_summary(candidate: dict[str, Any] | None) -> dict[str, Any]:
    candidate = candidate or {}
    dimensions = candidate.get("dimension_scores") or {}
    region = candidate.get("region_status") or {}
    return {
        "weighted_score": candidate.get("weighted_score"),
        "confidence": candidate.get("confidence") or "unknown",
        "dimensions": dimensions,
        "rows": [
            ("Skill 3 加權分", candidate.get("weighted_score", "unknown")),
            ("信心", candidate.get("confidence") or "unknown"),
            ("區域狀態", region.get("status") or "unknown"),
            ("建議低風險 Skill 4 驗證", _yes_no_unknown(_recommend_low_risk_validation(candidate))),
            ("達到 PoC 審查門檻", _yes_no_unknown(_eligible_for_poc_review(candidate))),
            ("成本", ((candidate.get("cost_estimate") or {}).get("status") or "unknown")),
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
                f"- 報價狀態：{quote.get('status') or 'unknown'}",
                f"- Quote ID：{quote.get('quote_id') or 'unknown'}",
                "- 結果：目前沒有已登錄且可稽核的費率模型，不填造金額。",
            ]
        )
        return lines

    expected = (quote.get("scenarios") or {}).get("expected") or {}
    price_range = quote.get("estimated_range_usd") or {}
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
            "",
            "### 報價假設與限制",
            "",
        ]
    )
    assumptions = expected.get("assumptions") or {}
    lines.append(
        f"- 預期情境使用 {assumptions.get('hours')} 小時、"
        f"{assumptions.get('active_gb')} GB active storage。"
    )
    lines.extend(f"- {item}" for item in quote.get("exclusions") or [])
    lines.append(f"- {quote.get('disclaimer')}")
    lines.extend(["", "### 官方價格來源", ""])
    lines.extend(
        f"- [{source.get('purpose')}]({source.get('url')})"
        for source in quote.get("sources") or []
    )
    return lines


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
            f"| Skill 3 公開牌價估算 | {estimated.get('status') or 'unknown'} | "
            f"{_format_money(estimated.get('expected_total_usd'))} | "
            f"{estimated.get('quote_id') or estimated.get('source') or 'unknown'} |"
        ),
    ]
    actual_source = actual.get("source_artifact") or actual.get("source_type") or "not_available"
    lines.append(
        f"| 可歸因實際帳務成本 | {actual.get('status') or 'unknown'} | "
        f"{_format_money(actual.get('amount_usd'))} | {actual_source} |"
    )
    lines.append(
        f"| 差異（實際 - 預估） | {reconciliation.get('status') or 'unknown'} | "
        f"{_format_money(reconciliation.get('delta_usd'))} | {reconciliation.get('rule')} |"
    )
    if actual.get("status") == "pending":
        lines.extend(["", f"- 實際成本狀態：pending。{actual.get('reason')}"])
        lines.append("- 不以 EC2 執行時間、CloudFormation 狀態或 runtime artifact 推算實際 AWS 帳務成本。")
    return lines


def _validation_summary(validation: dict[str, Any] | None, runtime: dict[str, Any] | None) -> dict[str, Any]:
    runtime = runtime or {}
    verification = runtime.get("verification") or {}
    cleanup = runtime.get("cleanup") or {}
    return {
        "rows": [
            ("Skill 4 validation", (validation or {}).get("validation_status") or "unknown"),
            ("CloudFormation", (runtime.get("deployment") or {}).get("stack_status") or "unknown"),
            ("自動化驗證", _verification_status(verification)),
            ("AWS Console review", (runtime.get("console_review") or {}).get("status") or "unknown"),
            ("cleanup", cleanup.get("status") or (validation or {}).get("cleanup_status") or "unknown"),
        ]
    }


def _verification_status(verification: dict[str, Any]) -> str:
    known = [
        value
        for key, value in verification.items()
        if key not in {"success_criteria", "recipe"} and isinstance(value, str)
    ]
    return "verified" if known and all(value == "verified" for value in known) else (", ".join(known) if known else "unknown")


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
    if (runtime or {}).get("cleanup", {}).get("status") != "verified":
        items.append("cleanup 尚未完成或尚未記錄。")
    return _dedupe(items)


def _next_reminders(candidate: dict[str, Any] | None, runtime: dict[str, Any] | None) -> list[str]:
    reminders = list((candidate or {}).get("stop_conditions") or [])
    if (runtime or {}).get("status") == "awaiting_console_review":
        reminders.append("完成 AWS Console review 後，才能執行受控 cleanup。")
    return _dedupe(reminders)


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
    else:
        entries.append(
            {
                "claim": "PoC 可歸因實際帳務成本",
                "type": "AWS billing evidence",
                "status": "pending",
                "source": str(actual.get("reason") or "billing artifact data gap"),
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
    return "unknown"


def _recommend_low_risk_validation(candidate: dict[str, Any]) -> bool:
    if "recommend_low_risk_validation" in candidate:
        return bool(candidate.get("recommend_low_risk_validation"))
    return bool(candidate.get("recommend_s4"))


def _eligible_for_poc_review(candidate: dict[str, Any]) -> bool:
    if "eligible_for_poc_review" in candidate:
        return bool(candidate.get("eligible_for_poc_review"))
    if "eligible_for_paid_poc_review" in candidate:
        return bool(candidate.get("eligible_for_paid_poc_review"))
    return bool(candidate.get("recommend_s4"))


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value).strip()))


def _format_number(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return str(value if value is not None else "unknown")
    return f"{float(value):.9f}".rstrip("0").rstrip(".")


def _format_money(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return str(value if value is not None else "unknown")
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    if "." not in text:
        return text + ".00"
    decimals = len(text.split(".", 1)[1])
    return text + ("0" * max(0, 2 - decimals))
