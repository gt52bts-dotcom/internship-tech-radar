"""Skill 5: render only recorded S1-S4 evidence into a professional report.

This module deliberately does not fetch sources or infer missing facts.  It
turns the immutable stage artifacts into one JSON report model, one Markdown
document, and one GUI-ready view model.  A renderer may change presentation,
but it must not invent a claim absent from these inputs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .pipeline_timing import build_stage_timings
from .s4_inventory import reconcile_quote_against_resources


def build_report(
    scan: dict[str, Any],
    compare: dict[str, Any] | None = None,
    evaluate: dict[str, Any] | None = None,
    validate: dict[str, Any] | None = None,
    runtime: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a source-bound Skill 5 artifact from the available stage artifacts."""

    inputs = {"S1": scan, "S2": compare, "S3": evaluate, "S4": validate}
    if runtime:
        inputs["S4 runtime"] = runtime
    issues = _input_issues(inputs)
    if (
        runtime
        and runtime.get("status") == "cleanup_verified"
        and not _is_abort_cleanup(runtime)
        and _runtime_requires_screenshot(runtime)
        and not _review_evidence_count(runtime)
    ):
        issues.append("missing_console_or_inventory_review_metadata")
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
        "architecture_and_significance": _architecture_and_significance(report_candidate),
        "evaluation": _evaluation_summary(selected),
        "cost_quote": _cost_quote(selected),
        "pre_cleanup_usage_snapshot": _pre_cleanup_usage_snapshot(runtime),
        "validation": _validation_summary(validation, runtime),
        "resource_inventory": _resource_inventory_section(runtime, _cost_quote(selected)),
        "permission_surface": _permission_surface_section(runtime),
        "stage_timings": build_stage_timings(
            _collect_stage_timings(runtime, validate, evaluate, compare, scan),
            _first_success(runtime, validate),
        ),
        "verified_facts": _verified_facts(scan, compare, selected, runtime),
        "unknown_or_not_verified": _unknowns(compare, selected, validation, runtime),
        "future_work": _future_work(report_candidate, selected, runtime),
        "reviewer_questions": _reviewer_questions(selected, runtime),
        "external_research": _external_research_directions(report_candidate, compare, selected, runtime),
        "related_articles_and_examples": _related_articles_and_application_examples(report_candidate, compare, selected),
        "related_topics": _related_topics(report_candidate, compare, selected),
        "stage_evidence": _stage_evidence(scan, compare, evaluate, validate, runtime, selected, status),
        "funnel": _funnel(scan, compare, evaluate, validate),
        "evidence_ledger": _evidence_ledger(scan, compare, selected, runtime),
    }
    report["human_summary"] = _human_summary(report, runtime)
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
    lines.extend(_render_architecture_and_significance(report["architecture_and_significance"]))
    lines.extend(_render_cost_quote(report["cost_quote"]))
    lines.extend(_render_pre_cleanup_usage_snapshot(report["pre_cleanup_usage_snapshot"]))
    lines.extend(["", "## 技術驗證", "", "| 檢查 | 狀態 |", "| --- | --- |"])
    for label, value in report["validation"]["rows"]:
        lines.append(f"| {label} | {value} |")
    lines.extend(["", "### 技術驗證狀態", ""])
    lines.extend(f"- {item}" for item in report["verified_facts"] or ["unknown"])
    lines.extend(["", "## 尚未驗證或證據不足", ""])
    lines.extend(f"- {item}" for item in report["unknown_or_not_verified"] or ["unknown"])
    lines.extend(_render_resource_inventory(report["resource_inventory"]))
    lines.extend(_render_permission_surface(report["permission_surface"]))
    lines.extend(_render_stage_timings(report["stage_timings"]))
    lines.extend(["", "## Future work", ""])
    lines.extend(f"- {item}" for item in report["future_work"] or ["尚無額外 Future work。"])
    lines.extend(_render_external_research(report["external_research"]))
    lines.extend(_render_related_articles_and_examples(report["related_articles_and_examples"]))
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


def render_markdown(report: dict[str, Any]) -> str:
    """Render the supervisor-facing report as a concise human summary."""

    candidate = report["candidate"]
    summary = report["human_summary"]
    quote = report["cost_quote"]
    lines = [
        f"# Skill 5 PoC 結案報告：{candidate['title'] or '未命名候選'}",
        "",
        "## 一眼看重點",
        "",
        f"- 結論：{summary['headline']}",
        f"- 做完發現：{summary['main_discovery']}",
        f"- 對公司的意義：{summary['business_meaning']}",
        f"- 現在不能宣稱：{summary['main_limit']}",
        "",
        "## 帳號、地區、權限能不能用",
        "",
        "| 問題 | 結論 | 證據 |",
        "| --- | --- | --- |",
    ]
    for row in summary["readiness_rows"]:
        lines.append(f"| {row['question']} | {row['answer']} | {row['evidence']} |")

    lines.extend(["", "## 我實際做完了什麼", ""])
    lines.extend(f"- {item}" for item in summary["completed_work"])

    if summary["poc_findings"]:
        lines.extend(["", "## 這次 PoC 證明了什麼", ""])
        lines.extend(f"- {item}" for item in summary["poc_findings"])

    lines.extend(["", "## 成本與清除狀態", ""])
    lines.append(f"- 預估成本：{summary['cost_summary']}")
    lines.append("- 成本性質：這是部署前用公開價格估算，不是 AWS 帳單。")
    lines.append(f"- 清除狀態：{summary['cleanup_summary']}")
    if quote.get("sources"):
        lines.append("- 價格來源：AWS 官方公開定價頁。")

    lines.extend(["", "## 還不能拿來宣稱的事", ""])
    lines.extend(f"- {item}" for item in summary["limits"])

    lines.extend(["", "## 下一步要補的決策證據", ""])
    lines.extend(f"- {item}" for item in summary["next_steps"])

    lines.extend(_render_related_articles_and_examples(report["related_articles_and_examples"]))

    if candidate.get("source_url") and candidate.get("source_url") != "unknown":
        lines.extend(["", "## 官方來源", "", f"- {candidate['source_url']}"])
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
            "human_summary": report["human_summary"],
        },
        "score": {
            "weighted_score": report["evaluation"].get("weighted_score"),
            "dimensions": dimensions,
        },
        "architecture_and_significance": report["architecture_and_significance"],
        "cost_quote": {**report["cost_quote"], "status_label": _display_status(report["cost_quote"].get("status"))},
        "pre_cleanup_usage_snapshot": {
            **report["pre_cleanup_usage_snapshot"],
            "status_label": _usage_snapshot_status_label(report["pre_cleanup_usage_snapshot"].get("status")),
        },
        "resource_inventory": report["resource_inventory"],
        "permission_surface": report["permission_surface"],
        "stage_timings": report["stage_timings"],
        "console_review": _gui_console_review(report),
        "validation_checks": checks,
        "verified_facts": report["verified_facts"],
        "unknown_or_not_verified": report["unknown_or_not_verified"],
        "future_work": report["future_work"],
        "reviewer_questions": report["reviewer_questions"],
        "external_research": report["external_research"],
        "related_articles_and_examples": report["related_articles_and_examples"],
        "related_topics": report["related_topics"],
        "stage_evidence": report["stage_evidence"],
        "evidence_ledger": report["evidence_ledger"],
        "funnel": report["funnel"],
    }


def _gui_console_review(report: dict[str, Any]) -> dict[str, Any]:
    """Keep screenshot metadata available to an authenticated review UI."""

    ledger = report.get("evidence_ledger") or []
    evidence_entry = next(
        (
            entry
            for entry in ledger
            if entry.get("claim") in {"Infrastructure Composer Console review", "CloudFormation resource inventory review"}
        ),
        None,
    )
    evidence_status = next((item[1] for item in report["validation"]["rows"] if item[0] == "Console / 資源盤點證據"), "not_recorded")
    return {
        "status": next((item[1] for item in report["validation"]["rows"] if item[0] == "AWS Console review"), "unknown"),
        "screenshot_status": evidence_status,
        "review_evidence_status": evidence_status,
        "evidence_recorded": evidence_entry is not None,
        "privacy": "Render review evidence only through an authenticated GUI or the active conversation; Git artifacts retain metadata only.",
    }


def _human_summary(report: dict[str, Any], runtime: dict[str, Any] | None) -> dict[str, Any]:
    candidate = report["candidate"]
    profile = _case_profile(candidate, candidate)
    deployment = (runtime or {}).get("deployment") or {}
    verification = (runtime or {}).get("verification") or {}
    cleanup = (runtime or {}).get("cleanup") or {}
    quote = report["cost_quote"]
    region = deployment.get("target_region") or quote.get("target_region") or report["evaluation"].get("target_region")
    deployed = deployment.get("stack_status") == "CREATE_COMPLETE"
    cleaned = cleanup.get("status") == "verified"
    completed_runtime = deployed or (runtime or {}).get("status") == "cleanup_verified"
    checks = _human_verification_findings(profile, verification)
    score = report["evaluation"].get("weighted_score")
    score_text = f"{score} / 5" if score is not None else "未記錄"
    expected_cost = quote.get("expected_total_usd")
    ceiling = quote.get("recommended_approval_ceiling_usd")
    cost_summary = (
        f"預期約 USD {_format_money(expected_cost)}，核准上限 USD {_format_money(ceiling)}"
        if expected_cost is not None or ceiling is not None
        else "未形成可用估算"
    )
    if completed_runtime and cleaned:
        headline = "本次受控 PoC 已完成、已人工確認，並已清除資源。"
    elif completed_runtime:
        headline = "本次 PoC 已能部署並通過核心檢查，但還沒有完整收尾。"
    elif _recommend_poc_from_report(report):
        headline = "已完成進 PoC 前評估，但尚未建立雲端資源。"
    else:
        headline = "本案例目前不建議硬做 PoC，重點是把停止原因講清楚。"

    readiness_rows = [
        {
            "question": "我們的 AWS 帳號可以建立這個 PoC 嗎？",
            "answer": "可以，已成功建立本次 PoC 所需資源。" if completed_runtime else "尚未證明，因為這份報告沒有成功部署紀錄。",
            "evidence": "CloudFormation 建立完成。" if deployed else "runtime 顯示 PoC 已完成清除。" if completed_runtime else "沒有成功建立資源的紀錄。",
        },
        {
            "question": "指定地區可以使用嗎？",
            "answer": f"可以，本次使用 {region}。" if completed_runtime and region else _region_answer(report, region),
            "evidence": "同一地區完成部署與驗證。" if completed_runtime and region else "目前只有評估紀錄，尚未用實際部署證明。",
        },
        {
            "question": "權限夠不夠？",
            "answer": "夠，至少足以完成本次最小 PoC。" if completed_runtime and checks else "尚未完整證明。",
            "evidence": _permission_evidence(checks, completed_runtime),
        },
        {
            "question": "資源有沒有收乾淨？",
            "answer": "已清除並回查。" if cleaned else "尚未清除或沒有清除證據。",
            "evidence": _cleanup_evidence(cleanup, cleaned),
        },
    ]

    completed_work = [
        "整理官方來源，確認這個功能想解決的技術問題。",
        f"用固定評分準則完成 Skill 3 評估，分數為 {score_text}。",
        f"用公開價格建立小型 PoC 成本估算：{cost_summary}。",
    ]
    if completed_runtime and region:
        completed_work.append(f"在 {region or '指定地區'} 建立受控 PoC 環境。")
    if checks:
        completed_work.append("跑完核心驗證：" + "；".join(checks) + "。")
    if (runtime or {}).get("console_review", {}).get("status") == "confirmed":
        completed_work.append("完成 AWS Console 人工確認。")
    if cleaned:
        completed_work.append("完成受控清除，避免測試資源繼續產生成本。")

    limits = _human_limits(profile, completed_runtime, cleaned)
    next_steps = _human_next_steps(profile, runtime)
    return {
        "headline": headline,
        "main_discovery": _main_discovery(profile, checks, completed_runtime),
        "business_meaning": _business_meaning(profile),
        "main_limit": limits[0],
        "readiness_rows": readiness_rows,
        "completed_work": completed_work,
        "poc_findings": checks,
        "cost_summary": cost_summary,
        "cleanup_summary": "已清除並回查。" if cleaned else "尚未完成清除回查。",
        "limits": limits,
        "next_steps": next_steps,
    }


def _region_from_evaluation(report: dict[str, Any]) -> str | None:
    for label, value in report["evaluation"].get("rows") or []:
        if "Region" in str(label) or "區域" in str(label) or "地區" in str(label):
            return str(value)
    return None


def _recommend_poc_from_report(report: dict[str, Any]) -> bool:
    for label, value in report["evaluation"].get("rows") or []:
        if "PoC" in str(label) and str(value).strip() in {"是", "true", "True", "yes"}:
            return True
    return report["conclusion"].get("status") == "poc_recommended_awaiting_approval"


def _region_answer(report: dict[str, Any], region: str | None) -> str:
    region_status = str(report["evaluation"].get("region_status") or "")
    if region_status == "available_ap_southeast_1":
        return f"Skill 3 評估顯示 {region or 'ap-southeast-1'} 可用，但還沒有部署證據。"
    if region and "available" in region:
        return "評估顯示可用，但還沒有部署證據。"
    if region:
        return f"目前紀錄為 {region}，需要人工確認。"
    return "未記錄可判讀的地區結論。"


def _permission_evidence(checks: list[str], deployed: bool) -> str:
    if deployed and checks:
        return "資源建立成功，且核心驗證通過。"
    if deployed:
        return "資源建立成功，但驗證項目不足。"
    return "沒有可用的部署與驗證紀錄。"


def _cleanup_evidence(cleanup: dict[str, Any], cleaned: bool) -> str:
    if not cleaned:
        return "沒有 cleanup verified 紀錄。"
    checks = cleanup.get("checks") or {}
    if not checks:
        return "cleanup 狀態已驗證。"
    readable = []
    if checks.get("cloudformation_stack") == "deleted":
        readable.append("CloudFormation stack 已刪除")
    if checks.get("versioned_test_bucket") == "emptied_before_stack_delete":
        readable.append("測試 bucket 已先清空")
    if checks.get("run_derived_resource_prefix") == "matched":
        readable.append("清除範圍符合本次測試前綴")
    return "；".join(readable) + "。" if readable else "cleanup 狀態已驗證。"


def _human_verification_findings(profile: dict[str, str], verification: dict[str, Any]) -> list[str]:
    if not verification:
        return []
    title = profile.get("display_name", "")
    findings: list[str] = []
    if "S3 Files" in title:
        if verification.get("source_to_mount") == "verified":
            findings.append("S3 內的物件可以從 EC2 掛載點讀到")
        if verification.get("mount_to_s3") == "verified":
            findings.append("從掛載點寫入的檔案可以回到 S3")
        if verification.get("ssm_status") == "Success":
            findings.append("EC2 測試指令可以透過受控方式執行成功")
    elif "Lambda" in title:
        if verification.get("cloudformation_reference_mode") == "verified":
            findings.append("CloudFormation 可以建立使用 REFERENCE 模式的 Lambda")
        if verification.get("lambda_invoke") == "verified":
            findings.append("Lambda 建立後可以成功 invoke")
    if findings:
        return findings[:5]
    for item in verification.get("success_criteria") or []:
        clean = str(item).strip().rstrip(".")
        if clean and clean not in findings:
            findings.append(clean)
    return findings[:5]


def _main_discovery(profile: dict[str, str], checks: list[str], deployed: bool) -> str:
    if not deployed:
        return "目前還停在評估階段，沒有實際部署後的發現。"
    if "S3 Files" in profile.get("display_name", ""):
        return "S3 Files 在本次帳號與地區中可以被建立，且 EC2 掛載點和 S3 bucket 之間能做最小讀寫驗證。"
    if "Lambda" in profile.get("display_name", ""):
        return "Lambda 可以直接參照自管 S3 code package，且建立後仍可正常執行。"
    return "本次最小 PoC 可以完成部署、核心驗證與清除。"


def _business_meaning(profile: dict[str, str]) -> str:
    if "S3 Files" in profile.get("display_name", ""):
        return "這代表它不只是新聞功能，而是有機會讓需要檔案介面的工作負載共用 S3 資料；下一步要判斷它是否撐得住真實檔案型工作負載。"
    if "Lambda" in profile.get("display_name", ""):
        return "這代表大量 Lambda 部署包可以改由自管 S3 bucket 當來源，可能改善部署與儲存治理；下一步要看 rollback、權限和生命週期管理是否可靠。"
    if "WorkSpaces" in profile.get("display_name", ""):
        return "重點不是先做 demo，而是確認桌面 agent 的成本、合規與人工停止機制是否值得進第二階段。"
    if "Quick" in profile.get("display_name", ""):
        return "重點是把產品宣稱轉成可部署流程；如果沒有 connector、權限與執行紀錄，就不應硬做 PoC。"
    return "這份報告把新聞宣稱轉成可檢查的技術決策，不只說看起來有用。"


def _human_limits(profile: dict[str, str], deployed: bool, cleaned: bool) -> list[str]:
    limits = ["這不是正式生產環境驗證，不能宣稱可直接導入公司正式系統。"]
    if deployed:
        limits.append("這次只證明最小 PoC 路徑可行，尚未測效能、可靠性、長時間運作或多人使用。")
    else:
        limits.append("這次沒有建立雲端資源，所以不能宣稱帳號權限、地區與實際部署都可用。")
    if not cleaned:
        limits.append("cleanup 沒有完整回查前，不能把報告當成 final 成功案例。")
    if "S3 Files" in profile.get("display_name", ""):
        limits.append("尚未證明同步延遲、POSIX 權限、一致性與錯誤復原是否符合真實工作負載。")
    if "Lambda" in profile.get("display_name", ""):
        limits.append("尚未證明 S3 object version rollback、source object 被刪除或撤權時的失敗行為。")
    limits.append("預估成本不是 AWS 帳單，不能拿來宣稱實際花費。")
    return limits


def _human_next_steps(profile: dict[str, str], runtime: dict[str, Any] | None) -> list[str]:
    if runtime and runtime.get("status") == "cleanup_verified":
        if "S3 Files" in profile.get("display_name", ""):
            return [
                "補一個小型真實工作負載測試：多檔案讀寫、同步延遲、權限錯誤與掛載失敗復原。",
                "外部查 S3 Files 的限制、定價與 troubleshooting，判斷它適合檔案共享、資料湖前處理，還是只適合展示型 PoC。",
            ]
        if "Lambda" in profile.get("display_name", ""):
            return [
                "補 rollback 測試：同一個 Lambda 從不同 S3 object version 切回舊部署包。",
                "外部查 REFERENCE 模式下的 bucket policy、code signing、生命週期刪除與 CI/CD 更新模式。",
            ]
    return [
        "先把尚未驗證的部署、地區、權限、成本或 cleanup 補成可檢查證據。",
        "只挑一個會改變導入判斷的問題做下一輪 PoC，不要為了展示而擴大範圍。",
    ]


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
        if _runtime_requires_screenshot(runtime) and not _review_evidence_count(runtime):
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
        if _resource_inventory_review_confirmed(runtime):
            return {
                "status": "validated_and_cleaned",
                "text": "實際 PoC 已通過自動化驗證與資源盤點人工確認，cleanup 回查也已完成。",
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


def _architecture_and_significance(candidate: dict[str, Any] | None) -> dict[str, Any]:
    """Render the S1 explanation layer without promoting it to verified fact.

    Key points are quoted from the page, so they stay source-backed.  The
    architecture sketch and the application contexts are derived, and the
    renderer keeps that distinction visible instead of flattening everything
    into one confident description.
    """

    explanation = (candidate or {}).get("explanation") or {}
    if not explanation:
        return {"status": "not_recorded", "note": "此 run 的 S1 artifact 沒有 explanation 區塊。"}
    significance = explanation.get("significance") or {}
    architecture = explanation.get("implementation_architecture") or {}
    components = architecture.get("core_components") or []
    return {
        "status": "recorded",
        "key_points": [
            {"id": item.get("id"), "point": item.get("point"), "derivation": item.get("derivation")}
            for item in explanation.get("key_points") or []
        ],
        "significance": {
            "status": significance.get("status"),
            "before": significance.get("before"),
            "after": significance.get("after"),
            "difference": significance.get("difference"),
            "derivation": significance.get("derivation"),
        },
        "architecture": {
            "status": architecture.get("status"),
            "data_flow": architecture.get("data_flow"),
            "stated_components": [item for item in components if item.get("stated_in_source")],
            "unstated_components": [item for item in components if not item.get("stated_in_source")],
            "minimal_poc_shape": architecture.get("minimal_poc_shape") or [],
        },
        "application_contexts": explanation.get("possible_application_contexts") or [],
        "rule": "重點為原文引述；架構草案與應用場景為推導內容，不列入已證實的事實。",
    }


def _render_architecture_and_significance(section: dict[str, Any]) -> list[str]:
    if section.get("status") != "recorded":
        return []
    lines = ["", "## 這個功能在做什麼", ""]
    significance = section.get("significance") or {}
    if significance.get("status") == "derived":
        lines.extend(
            [
                f"- 以前：{significance.get('before')}",
                f"- 現在：{significance.get('after')}",
                f"- 差別：{significance.get('difference')}",
                "- 以上為原文壓縮整理，非實測結果。",
            ]
        )
    else:
        lines.append("- 取回的頁面文字不足以整理改變前後的對比。")
    if section.get("key_points"):
        lines.extend(["", "### 原文重點", ""])
        lines.extend(f"- {item['point']}" for item in section["key_points"])
    architecture = section.get("architecture") or {}
    lines.extend(["", "## 實作架構主體（推導草案）", ""])
    if architecture.get("status") == "drafted":
        lines.append(f"- 資料流：{architecture.get('data_flow')}")
        lines.append("- 原文明述的元件：" + "、".join(
            f"{item['service']}（{item['role']}）" for item in architecture.get("stated_components") or []
        ))
        unstated = architecture.get("unstated_components") or []
        if unstated:
            lines.append("- 原文未提及但實作必需：" + "、".join(
                f"{item['service']}（{item['role']}）" for item in unstated
            ))
        if architecture.get("minimal_poc_shape"):
            lines.extend(["", "### 最小 PoC 形狀", ""])
            lines.extend(f"- {step}" for step in architecture["minimal_poc_shape"])
    else:
        lines.append("- 未偵測到受支援的 AWS 服務，無法草擬架構。")
    contexts = section.get("application_contexts") or []
    if contexts:
        lines.extend(["", "## 可能的應用場景", ""])
        for item in contexts:
            tag = "原文明述" if item.get("derivation") == "source_verbatim" else "推論"
            lines.append(f"- （{tag}）{item.get('context')}")
    lines.append("")
    lines.append("> 架構草案與應用場景為推導內容，未經驗證，不列入已證實的事實。")
    return lines


def _collect_stage_timings(*artifacts: dict[str, Any] | None) -> dict[str, Any]:
    """Gather the accumulated per-stage record from whichever artifact carries it.

    Timings ride along inside the artifacts, and the latest stage holds the most
    complete copy, so later artifacts are merged over earlier ones.
    """

    merged: dict[str, Any] = {}
    for artifact in reversed([a for a in artifacts if a]):
        merged.update(artifact.get("stage_timings") or {})
    return merged


def _first_success(*artifacts: dict[str, Any] | None) -> str | None:
    for artifact in artifacts:
        if artifact and artifact.get("first_success_at"):
            return str(artifact["first_success_at"])
    return None


def _resource_inventory_section(runtime: dict[str, Any] | None, quote: dict[str, Any]) -> dict[str, Any]:
    """Render the Skill 4 inventory and its reconciliation against the quote."""

    inventory = (runtime or {}).get("resource_inventory") or {}
    if not inventory:
        return {"status": "not_recorded", "note": "此 run 沒有記錄 CloudFormation 資源盤點。"}
    recorded = inventory.get("quote_reconciliation") or reconcile_quote_against_resources(
        quote, inventory.get("resources") or []
    )
    return {
        "status": "recorded",
        "stack_name": inventory.get("stack_name"),
        "region": inventory.get("region"),
        "captured_at": inventory.get("captured_at"),
        "resource_count": inventory.get("resource_count"),
        "inventory_sha256": inventory.get("inventory_sha256"),
        "resources": inventory.get("resources") or [],
        "reconciliation": recorded,
        "rule": "盤點為 CloudFormation API 回報的結構化資料，可由程式驗證；人工確認的是同一份 JSON。",
    }


def _permission_surface_section(runtime: dict[str, Any] | None) -> dict[str, Any]:
    inventory = (runtime or {}).get("resource_inventory") or {}
    surface = inventory.get("permission_surface") or {}
    if not surface:
        return {"status": "not_recorded", "note": "此 run 未記錄實際使用的 IAM action。"}
    return surface


def _render_resource_inventory(section: dict[str, Any]) -> list[str]:
    if section.get("status") != "recorded":
        return []
    reconciliation = section.get("reconciliation") or {}
    labels = {
        "matched": "相符",
        "deployed_not_quoted": "報價未涵蓋",
        "quoted_not_deployed": "報價列了但未部署",
        "quoted_implicit_resource": "報價已列，屬隱含資源",
    }
    lines = ["", "## 報價 vs 實際部署資源", "", f"- 對照結果：{_display_status(reconciliation.get('status'))}", ""]
    lines.append("| 資源類型 | 報價單有計價 | 實際部署 | 判定 |")
    lines.append("| --- | :---: | :---: | --- |")
    for row in reconciliation.get("rows") or []:
        lines.append(
            f"| {row['resource_type']} | {'✓' if row['quoted'] else '✗'} | "
            f"{'✓' if row['deployed'] else '✗'} | {labels.get(row['verdict'], row['verdict'])} |"
        )
    if reconciliation.get("deployed_not_quoted"):
        lines.append("")
        lines.append(
            "> 報價單漏列了實際會建立的資源："
            + "、".join(reconciliation["deployed_not_quoted"])
            + "。必須修正報價單的資源清單，不能只調整金額。"
        )
    lines.extend(["", "## Skill 4 資源盤點", ""])
    lines.append(f"- Stack：{section.get('stack_name') or '未記錄'}（{section.get('region') or '未記錄'}）")
    lines.append(f"- 盤點時間：{section.get('captured_at') or '未記錄'}；資源數：{section.get('resource_count')}")
    lines.append(f"- 盤點雜湊：{section.get('inventory_sha256') or '未記錄'}")
    lines.extend(["", "| Logical ID | 資源類型 | 狀態 | 實體識別（已遮蔽） |", "| --- | --- | --- | --- |"])
    for item in section.get("resources") or []:
        lines.append(
            f"| {item['logical_id']} | {item['resource_type']} | "
            f"{item['status']} | {item['physical_id_redacted']} |"
        )
    return lines


def _render_permission_surface(surface: dict[str, Any]) -> list[str]:
    if surface.get("status") != "recorded":
        return []
    lines = ["", "## 實際權限面", "", f"- 實際觸發 {surface.get('action_count')} 個 IAM action，涵蓋服務："
             + "、".join(surface.get("services") or []), ""]
    lines.extend(f"- `{action}`" for action in surface.get("actions") or [])
    lines.extend(["", f"> {surface.get('note')}"])
    return lines


def _render_stage_timings(timings: dict[str, Any]) -> list[str]:
    rows = [row for row in timings.get("rows") or [] if row.get("status") == "recorded"]
    if not rows:
        return []
    lines = ["", "## 各階段耗時", "", "| 階段 | 程式耗時（秒） | 人工等待（秒） | 人工關卡 |", "| --- | ---: | ---: | --- |"]
    for row in rows:
        lines.append(
            f"| {row['stage']} | {row.get('machine_seconds') if row.get('machine_seconds') is not None else '未記錄'} "
            f"| {row.get('human_wait_seconds') if row.get('human_wait_seconds') is not None else '未記錄'} "
            f"| {row.get('human_gate') or '—'} |"
        )
    lines.append("")
    lines.append(
        f"- 程式總耗時 {timings.get('machine_seconds_total')} 秒；人工等待總計 "
        f"{timings.get('human_wait_seconds_total')} 秒。"
    )
    if timings.get("human_share") is not None:
        lines.append(f"- 人工等待佔總時間 {round(timings['human_share'] * 100, 1)}%。")
    if timings.get("time_to_first_success_seconds") is not None:
        lines.append(f"- 從 S1 開始到首次驗證通過：{timings['time_to_first_success_seconds']} 秒。")
    lines.append(f"- {timings.get('reading_note')}")
    return lines


def _source_summary_candidates(candidate: dict[str, Any]) -> list[str]:
    fetched = candidate.get("fetched_source") or {}
    dimensions = candidate.get("comparison_dimensions") or {}
    capability_excerpts = (
        (dimensions.get("source_backed_capabilities") or {}).get("excerpts")
        or (dimensions.get("source_backed_capabilities") or {}).get("source_excerpts")
        or []
    )
    explanation = candidate.get("explanation") or {}
    key_points = [item.get("point") for item in explanation.get("key_points") or []]
    values = [
        *key_points,
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
        "dimensions": dimensions,
        "region_status": region.get("status"),
        "target_region": region.get("target_region"),
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
        "rule": "cleanup 前未提供即時用量快照；新版 Skill 5 不把 runtime facts 轉成實際 AWS 成本。",
    }


def _usage_snapshot_status_label(value: Any) -> str:
    labels = {
        "captured": "已擷取",
        "partial": "部分擷取",
        "unavailable": "無法擷取",
        "not_recorded": "未記錄",
        "not_billing_evidence": "非帳務證據",
        "consistent": "報價與實際部署一致",
        "quote_incomplete": "報價漏列實際資源",
        "quote_lists_undeployed_resources": "報價列了未部署的資源",
        "no_quote_resource_list": "報價未宣告資源清單",
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
            "- 性質：這是 runtime facts，不是 AWS 帳單；新版 Skill 5 不回報實際 AWS 成本。",
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
            ("Console / 資源盤點證據", _review_evidence_status(runtime)),
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
    if (runtime or {}).get("deployment", {}).get("stack_status") == "CREATE_COMPLETE":
        facts.append("CloudFormation stack 已達 CREATE_COMPLETE。")
    if _resource_inventory_review_confirmed(runtime):
        facts.append("AWS review 已以結構化資源盤點透過 GUI 或對話交由具名人員確認。")
    elif _console_screenshot_count(runtime):
        screenshot_count = _console_screenshot_count(runtime)
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
) -> list[str]:
    items = list(((candidate or {}).get("evidence_refs") or {}).get("evidence_limits") or [])
    if ((candidate or {}).get("cost_estimate") or {}).get("status") != "estimated":
        items.append("官方定價或實際成本尚未在 artifact 中證實。")
    items.append("報價單是依公開牌價與明列用量假設產生的預估；本流程不進行預估與實際帳務成本比對，金額未經任何 AWS 帳務資料驗證。")
    if (runtime or {}).get("console_review", {}).get("status") != "confirmed":
        items.append("AWS Console review 尚未完成或尚未記錄。")
    elif (runtime or {}).get("schema_version") == "s4.runtime-evidence.v3" and not _review_evidence_count(runtime):
        items.append("此 PoC runtime 尚未記錄 Console 截圖或結構化資源盤點證據。")
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
) -> list[str]:
    items: list[str] = []
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
    questions.append("報價單的計費方式與公式是否正確反映這個 recipe 會建立的每一項資源？有沒有漏算的常駐或用量型費用？")
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
    topics.extend(["AWS Pricing Calculator", "CloudFormation", "PoC cleanup", "Future work"])
    return _dedupe([_topic_label(item) for item in topics if item])


def _future_work(
    report_candidate: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
) -> list[str]:
    """Produce decision-oriented next work, not generic closing homework."""

    profile = _case_profile(report_candidate, candidate)
    items: list[str] = []
    if runtime and runtime.get("status") == "cleanup_verified":
        items.append(
            f"把下一輪 PoC 從「資源能建立」推進到「{profile['decision_question']}」；先外部搜尋 {profile['search_anchor']} 的實務限制，再只挑一個會改變導入判斷的情境重跑。"
        )
        items.append(
            f"補一個邊界測試：{profile['boundary_test']}。成功標準要能被 log、resource inventory 或應用輸出證明，不要只看 Console 畫面。"
        )
    elif runtime and runtime.get("status") == "awaiting_console_review":
        items.append(
            "先完成 Console/resource inventory 人工確認與 cleanup，再討論下一輪；未收尾的 runtime 不能拿來延伸成新 PoC。"
        )
        items.append(
            f"收尾後再搜尋 {profile['search_anchor']} 的常見失敗模式，決定下一輪是否要測 {profile['boundary_test']}。"
        )
    elif _recommend_poc(candidate or {}):
        items.append(
            f"進 Skill 4 前先外部搜尋 {profile['search_anchor']} 的部署限制、權限邊界、計價陷阱與 rollback 做法，確認 PoC 問題不是只在重複官方範例。"
        )
        items.append(
            f"把 PoC 問題改寫成一句可驗收的決策問題：{profile['decision_question']}。回答不出來就不要開資源。"
        )
    else:
        blockers = ", ".join(_poc_blockers(candidate)) or "目前證據不足"
        items.append(
            f"不要硬做 PoC；先針對停止原因「{blockers}」外部搜尋官方開發文件、管理指南、定價、quota、權限與範例架構。"
        )
        items.append(
            f"只有找到可部署資源清單、成功條件與 cleanup 路徑後，才回來寫 Skill 4 recipe；優先驗證 {profile['decision_question']}。"
        )
    items.append(
        "把搜尋結果整理成一張「值得做 / 不值得做」判斷卡：新找到的證據、它改變哪個假設、下一輪最小 PoC 要測什麼、仍不能宣稱什麼。"
    )
    return _dedupe(items)


def _external_research_directions(
    report_candidate: dict[str, Any] | None,
    compare: dict[str, Any] | None,
    selected: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
) -> dict[str, Any]:
    profile = _case_profile(report_candidate, selected)
    return {
        "status": "search_required",
        "claim_boundary": "以下是建議外部搜尋方向，不是已驗證結論；採用前必須把找到的來源補回 S1/S2/S3 artifacts。",
        "directions": [
            {
                "direction": "找出真正值得測的使用情境",
                "query": profile["scenario_query"],
                "why": "避免下一輪只是重跑官方 demo；要找到一個貼近使用者流程、資料型態或治理限制的場景。",
                "useful_evidence": "官方範例、架構圖、限制說明、customer story 或 workshop，能指出資料流、使用者、成功標準與限制。",
            },
            {
                "direction": "查部署與權限邊界",
                "query": profile["governance_query"],
                "why": "Skill 4 真正有價值的是證明帳號、Region、IAM、網路與 cleanup 邊界可控。",
                "useful_evidence": "明確列出 IAM action、resource policy、network path、Region 支援、quota 或 rollback/cleanup 方法的文件。",
            },
            {
                "direction": "查成本和失敗模式",
                "query": profile["cost_risk_query"],
                "why": "下一輪 PoC 應該測最可能讓決策翻盤的成本或可靠性風險。",
                "useful_evidence": "定價頁、pricing example、troubleshooting guide、service quota、known limitation 或監控指標。",
            },
        ],
        "after_search_action": (
            "把搜尋結果拆成三類：可直接補強 Skill 4 recipe、只適合列為 reviewer question、"
            "以及會讓本候選暫停的 blocker。"
        ),
    }


def _render_external_research(section: dict[str, Any]) -> list[str]:
    lines = ["", "## 外部搜尋與延伸閱讀方向", ""]
    lines.append(f"- 證據邊界：{section.get('claim_boundary')}")
    for item in section.get("directions") or []:
        lines.extend(
            [
                f"- {item['direction']}：搜尋 `{item['query']}`",
                f"  - 為什麼：{item['why']}",
                f"  - 有用證據長相：{item['useful_evidence']}",
            ]
        )
    if section.get("after_search_action"):
        lines.append(f"- 搜完後動作：{section['after_search_action']}")
    return lines


def _related_articles_and_application_examples(
    report_candidate: dict[str, Any] | None,
    compare: dict[str, Any] | None,
    selected: dict[str, Any] | None,
) -> dict[str, Any]:
    profile = _case_profile(report_candidate, selected)
    title = str((report_candidate or selected or {}).get("title") or "unknown")
    source_url = (
        (report_candidate or {}).get("source_url")
        or (selected or {}).get("source_url")
        or ""
    )
    articles: list[dict[str, str]] = []
    if source_url:
        articles.append(
            {
                "title": f"{title} 原始來源文章",
                "url": source_url,
                "type": "已取得來源",
                "why_it_matters": "這是本次 S1-S5 證據鏈的起點，只能支持原文已明確寫出的主張。",
                "next_role": "預言者雷達",
            }
        )
    articles.extend(
        [
            {
                "title": f"{profile['display_name']} 官方實作文件或 workshop",
                "url": "",
                "query": profile["scenario_query"],
                "type": "待外部搜尋",
                "why_it_matters": "補足原始新聞沒有講清楚的部署步驟、架構限制與操作條件。",
                "next_role": "架構師 / 驗證者",
            },
            {
                "title": f"{profile['display_name']} 權限、治理與 rollback 案例",
                "url": "",
                "query": profile["governance_query"],
                "type": "待外部搜尋",
                "why_it_matters": "判斷它能不能從展示型 PoC 進到受控導入，尤其是 IAM、Region、cleanup 與回復策略。",
                "next_role": "治理者 / 驗證者",
            },
        ]
    )
    return {
        "status": "articles_and_examples_required",
        "claim_boundary": (
            "此節把已取得來源與待外搜文章分開；待外搜項目不是已驗證結論，找到來源後必須回填到 S1/S2/S3 才能升級為證據。"
        ),
        "articles": articles,
        "application_examples": _application_examples_for_profile(profile),
    }


def _application_examples_for_profile(profile: dict[str, str]) -> list[dict[str, str]]:
    name = profile["display_name"]
    if name == "S3 Files":
        return [
            {
                "scenario": "把既有 EC2 檔案讀寫工作負載接到 S3 bucket",
                "how_it_uses_candidate": "用 S3 Files mount 方式讓應用程式先維持檔案系統介面，再觀察同步、延遲與一致性限制。",
                "decision_it_changes": "決定下一輪要測真實檔案操作情境，不只是證明 EC2 可以 mount。",
                "next_role": "驗證者",
            },
            {
                "scenario": "資料湖前處理或批次匯入暫存區",
                "how_it_uses_candidate": "讓工具用檔案介面寫入資料，再回到 S3 bucket 做後續分析或治理。",
                "decision_it_changes": "判斷 S3 Files 適合過渡型整合，還是應直接改寫成原生 S3 API。",
                "next_role": "架構師",
            },
        ]
    if name == "Lambda self-managed S3 code storage":
        return [
            {
                "scenario": "大型 Lambda deployment package 的版本治理",
                "how_it_uses_candidate": "把函式程式碼保留在 S3 object，讓版本、生命週期、bucket policy 與 rollback 變成可審核對象。",
                "decision_it_changes": "決定下一輪要測 S3 object version rollback、bucket policy 與 CI/CD 更新流程。",
                "next_role": "治理者 / 落地者",
            },
            {
                "scenario": "跨團隊共用部署 artifact 的控管流程",
                "how_it_uses_candidate": "把部署包來源與存取權限獨立出來，讓平台團隊可以檢查誰能更新、誰能讀取、何時清除。",
                "decision_it_changes": "判斷它是單純便利功能，還是能支撐正式部署治理。",
                "next_role": "平台架構師",
            },
        ]
    if name == "WorkSpaces Applications agent access":
        return [
            {
                "scenario": "AI agent 操作受控桌面應用程式",
                "how_it_uses_candidate": "先驗證 AgentAccessConfig 與人類可觀察 / 可停止邊界，再決定是否進入完整桌面工作流。",
                "decision_it_changes": "決定是否值得付出 full session 成本與更高治理成本。",
                "next_role": "治理者 / 產品負責人",
            }
        ]
    if name == "Amazon Quick Suite":
        return [
            {
                "scenario": "企業知識問答與 action connector 工作流",
                "how_it_uses_candidate": "需要找到可部署 API、connector、權限與 usage metric 後，才可能變成可驗證 PoC。",
                "decision_it_changes": "若只找到產品宣傳，維持 stop；若找到可重現 recipe，才回到 Skill 3 重評。",
                "next_role": "評估者 / 治理者",
            }
        ]
    return [
        {
            "scenario": f"{name} 的目標工作負載導入情境",
            "how_it_uses_candidate": "用外部文章或案例補足原始來源未說明的架構、限制、成本與權限條件。",
            "decision_it_changes": "決定下一輪是補 Skill 3 證據、建立 Skill 4 recipe，還是維持 stop decision。",
            "next_role": "評估者 / 架構師",
        }
    ]


def _render_related_articles_and_examples(section: dict[str, Any]) -> list[str]:
    lines = ["", "## 相關文章與應用實例", ""]
    lines.append(f"- 證據邊界：{section.get('claim_boundary')}")
    lines.extend(["", "### 相關文章", ""])
    for item in section.get("articles") or []:
        target = item.get("url") or f"搜尋：`{item.get('query', '')}`"
        lines.append(f"- {item['title']}（{item['type']}）：{target}")
        lines.append(f"  - 為什麼要看：{item['why_it_matters']}")
        lines.append(f"  - 會交給誰用：{item['next_role']}")
    lines.extend(["", "### 應用實例", ""])
    for item in section.get("application_examples") or []:
        lines.append(f"- {item['scenario']}")
        lines.append(f"  - 怎麼用在本案例：{item['how_it_uses_candidate']}")
        lines.append(f"  - 會改變的判斷：{item['decision_it_changes']}")
        lines.append(f"  - 下一個角色：{item['next_role']}")
    return lines


def _related_topics(
    report_candidate: dict[str, Any] | None,
    compare: dict[str, Any] | None,
    selected: dict[str, Any] | None,
) -> list[str]:
    profile = _case_profile(report_candidate, selected)
    services = _services_for_candidate(report_candidate, selected)
    topics = [
        f"{profile['display_name']} 官方 developer guide / administration guide",
        f"{profile['display_name']} pricing、quota、Region support",
        f"{profile['display_name']} IAM/resource policy/security best practices",
        f"{profile['display_name']} troubleshooting、known limitations、rollback/cleanup",
    ]
    topics.extend(f"{service} 與本 PoC 的整合模式" for service in services[:4])
    return _dedupe(topics)


def _case_profile(report_candidate: dict[str, Any] | None, selected: dict[str, Any] | None) -> dict[str, str]:
    candidate = {**(report_candidate or {}), **(selected or {})}
    title = str(candidate.get("title") or "this AWS candidate")
    recipe = str((((candidate.get("cost_estimate") or {}).get("quote") or {}).get("recipe")) or "")
    services = " ".join(_services_for_candidate(report_candidate, selected)).lower()
    text = " ".join([title, recipe, services]).lower()

    if "s3_files" in recipe or "s3 files" in text:
        return {
            "display_name": "S3 Files",
            "search_anchor": "S3 Files + EC2 mount + S3 bucket synchronization",
            "decision_question": "S3 Files 是否能支撐真實檔案型工作負載，而不只是證明 EC2 可以 mount",
            "boundary_test": "測同步延遲、POSIX 權限、mount target/AZ 配置錯誤、以及 S3 API 與檔案操作交錯時的一致性",
            "scenario_query": "S3 Files EC2 mount workload migration NFS S3 bucket architecture",
            "governance_query": "S3 Files IAM access point mount target VPC security group permissions",
            "cost_risk_query": "S3 Files pricing troubleshooting consistency latency mount failure",
        }
    if "lambda_self_managed" in recipe or ("lambda" in text and "s3" in text and "code" in text):
        return {
            "display_name": "Lambda self-managed S3 code storage",
            "search_anchor": "Lambda self-managed S3 code storage + deployment artifact governance",
            "decision_question": "REFERENCE 模式是否改善大型部署包/多函數 artifact 管理，同時仍保留 rollback、安全與生命週期控管",
            "boundary_test": "測 S3 object version rollback、bucket policy 最小權限、source object 被刪除或撤權時的失敗行為、以及 CI/CD 更新流程",
            "scenario_query": "Lambda self-managed S3 code storage deployment artifact rollback versioning",
            "governance_query": "Lambda S3ObjectStorageMode REFERENCE bucket policy GetObjectVersion code signing",
            "cost_risk_query": "Lambda self-managed S3 code storage lifecycle quota cold start troubleshooting",
        }
    if "workspaces" in text or "appstream" in text:
        return {
            "display_name": "WorkSpaces Applications agent access",
            "search_anchor": "WorkSpaces Applications agent access + MCP + human stop controls",
            "decision_question": "桌面代理是否能在可觀察、可停止、可稽核的條件下完成一個真實桌面任務",
            "boundary_test": "測 MCP session、human observe/stop、CloudTrail/CloudWatch 可觀測性、Windows user fee 觸發條件與 cleanup 不可回復成本",
            "scenario_query": "WorkSpaces Applications AI agents MCP desktop workflow governance",
            "governance_query": "WorkSpaces Applications AgentAccessConfig IAM CloudTrail CloudWatch human stop",
            "cost_risk_query": "WorkSpaces Applications AI agents pricing MCP session Windows user fee",
        }
    if "quick" in text:
        return {
            "display_name": "Amazon Quick Suite",
            "search_anchor": "Amazon Quick integrations + action connectors + governance",
            "decision_question": "Quick Suite 是否有足夠可配置的 connector、資料邊界與治理控制，能把一個業務流程變成可驗證 PoC",
            "boundary_test": "找出一個最小流程，要求明確資料來源、action connector、權限、執行紀錄、usage metrics 與清除方式",
            "scenario_query": "Amazon Quick Suite Quick Automate action connectors knowledge base workflow example",
            "governance_query": "Amazon Quick integrations custom permissions governance action connector APIs",
            "cost_risk_query": "Amazon Quick Suite pricing usage metrics quotas Quick Automate Quick Research",
        }
    return {
        "display_name": title,
        "search_anchor": f"{title} implementation architecture pricing security",
        "decision_question": "這項技術是否能用一個小型、可清除、可驗收的 PoC 改變導入判斷",
        "boundary_test": "測最小部署、最小權限、失敗回復、成本驅動與 cleanup 可重現性",
        "scenario_query": f"{title} reference architecture customer use case workshop",
        "governance_query": f"{title} IAM permissions security region quota deployment guide",
        "cost_risk_query": f"{title} pricing troubleshooting limitations cleanup",
    }


def _services_for_candidate(
    report_candidate: dict[str, Any] | None,
    selected: dict[str, Any] | None,
) -> list[str]:
    services: list[str] = []
    for source in (report_candidate or {}, selected or {}):
        services.extend(str(item) for item in source.get("related_aws_services") or [])
        scope = ((source.get("comparison_dimensions") or {}).get("technology_scope") or {})
        services.extend(str(item) for item in scope.get("services_detected") or [])
        quote = ((source.get("cost_estimate") or {}).get("quote") or {})
        services.extend(str(item) for item in quote.get("detected_services") or [])
    return _dedupe([_topic_label(item) for item in services if item])


def _poc_blockers(candidate: dict[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    blockers.extend(str(item) for item in (candidate or {}).get("blockers") or [])
    blockers.extend(str(item) for item in (candidate or {}).get("governance_flags") or [])
    readiness = (candidate or {}).get("s4_readiness") or {}
    if readiness.get("can_enter_skill4") is False and readiness.get("readiness_status"):
        blockers.append(str(readiness["readiness_status"]))
    recipe = (candidate or {}).get("poc_recipe") or {}
    if recipe.get("deployable_recipe_registered") is False:
        blockers.append("no_deployable_recipe")
    return _dedupe(blockers)


def _stage_evidence(
    scan: dict[str, Any],
    compare: dict[str, Any] | None,
    evaluate: dict[str, Any] | None,
    validate: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
    selected: dict[str, Any] | None,
    report_status: str,
) -> list[dict[str, str]]:
    candidate_id = (selected or {}).get("candidate_id")
    s2_candidate = _find_candidate((compare or {}).get("candidates") or [], candidate_id)
    quote = _cost_quote(selected)
    validation = _matching_candidate(validate, candidate_id)
    usage_snapshot = _pre_cleanup_usage_snapshot(runtime)
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
                f"cost_basis=公開牌價預估（未與帳務比對）"
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
) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    source_url = (candidate or {}).get("source_url") or "unknown"
    if source_url != "unknown":
        entries.append({"claim": "候選技術的公開來源", "type": "source-backed fact", "status": "recorded", "source": source_url})
    for key, value in ((runtime or {}).get("verification") or {}).items():
        if key != "success_criteria":
            entries.append({"claim": key, "type": "runtime evidence", "status": str(value), "source": "S4 runtime artifact"})
    if _resource_inventory_review_confirmed(runtime):
        evidence = ((runtime or {}).get("console_review") or {}).get("evidence") or {}
        entries.append(
            {
                "claim": "CloudFormation resource inventory review",
                "type": "human-reviewed structured inventory evidence",
                "status": "confirmed",
                "source": f"S4 resource inventory evidence ({evidence.get('inventory_sha256') or 'hash recorded'})",
            }
        )
    else:
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
    if isinstance(evidence, dict) and evidence.get("schema_version") == "s4.resource-inventory-review.v1":
        return 0
    screenshots = evidence.get("screenshots") if isinstance(evidence, dict) else None
    return len(screenshots) if isinstance(screenshots, list) else 0


def _resource_inventory_review_confirmed(runtime: dict[str, Any] | None) -> bool:
    evidence = ((runtime or {}).get("console_review") or {}).get("evidence") or {}
    return isinstance(evidence, dict) and evidence.get("schema_version") == "s4.resource-inventory-review.v1"


def _review_evidence_count(runtime: dict[str, Any] | None) -> int:
    if _resource_inventory_review_confirmed(runtime):
        return 1
    return _console_screenshot_count(runtime)


def _console_display_channel_confirmed(runtime: dict[str, Any] | None) -> bool:
    return ((runtime or {}).get("console_review") or {}).get("display_channel_confirmed") in {"gui", "conversation"}


def _is_abort_cleanup(runtime: dict[str, Any] | None) -> bool:
    cleanup = (runtime or {}).get("cleanup") or {}
    review = (runtime or {}).get("console_review") or {}
    return cleanup.get("cleanup_mode") == "abort_without_console_review" or review.get("status") == "skipped_for_cost_control"


def _runtime_requires_screenshot(runtime: dict[str, Any] | None) -> bool:
    return (runtime or {}).get("schema_version") == "s4.runtime-evidence.v3"


def _console_screenshot_status(runtime: dict[str, Any] | None) -> str:
    if _resource_inventory_review_confirmed(runtime):
        return "已用資源盤點經人類確認（1 份）"
    count = _console_screenshot_count(runtime)
    if count:
        if _console_display_channel_confirmed(runtime):
            return f"已截圖並經人類確認（{count} 張）"
        return f"已截圖但尚未確認顯示管道（{count} 張）"
    return _display_status(((runtime or {}).get("console_review") or {}).get("evidence_status") or "not_recorded")


def _review_evidence_status(runtime: dict[str, Any] | None) -> str:
    return _console_screenshot_status(runtime)


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
