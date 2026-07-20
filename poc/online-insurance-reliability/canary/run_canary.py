from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "out"


class StepFailed(Exception):
    def __init__(
        self,
        step: str,
        message: str,
        evidence: dict[str, Any] | None = None,
        steps: list[dict[str, Any]] | None = None,
    ):
        super().__init__(message)
        self.step = step
        self.message = message
        self.evidence = evidence or {}
        self.steps = steps or []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synthetic canary for the mock online insurance flow.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8088")
    parser.add_argument("--scenario-label", default="manual")
    parser.add_argument("--timeout-ms", type=int, default=1500)
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR))
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def http_request(method: str, url: str, timeout_ms: int, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None
    headers = {"User-Agent": "insurance-reliability-canary/0.1"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url, data=body, headers=headers, method=method)
    started = time.perf_counter()
    try:
        with request.urlopen(req, timeout=timeout_ms / 1000) as response:
            raw = response.read()
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            content_type = response.headers.get("Content-Type", "")
            text = raw.decode("utf-8", errors="replace")
            parsed: Any = None
            if "application/json" in content_type:
                parsed = json.loads(text)
            return {
                "ok": 200 <= response.status < 300,
                "status_code": response.status,
                "duration_ms": duration_ms,
                "content_type": content_type,
                "body_text": text,
                "json": parsed,
            }
    except error.HTTPError as exc:
        raw = exc.read()
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "ok": False,
            "status_code": exc.code,
            "duration_ms": duration_ms,
            "content_type": exc.headers.get("Content-Type", ""),
            "body_text": raw.decode("utf-8", errors="replace"),
            "json": try_parse_json(raw),
        }
    except (TimeoutError, socket.timeout) as exc:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        raise StepFailed("network_timeout", f"Request timed out after {duration_ms} ms", {"exception": repr(exc)})
    except error.URLError as exc:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        raise StepFailed("network_unreachable", f"Request failed after {duration_ms} ms: {exc}", {"exception": repr(exc)})


def try_parse_json(raw: bytes) -> Any:
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def run_flow(base_url: str, timeout_ms: int) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []

    try:
        homepage = http_request("GET", f"{base_url}/", timeout_ms)
    except StepFailed as exc:
        raise StepFailed("homepage_load", exc.message, exc.evidence, steps)
    steps.append({"name": "homepage_load", **summarize_response(homepage)})
    if not homepage["ok"] or "線上投保" not in homepage["body_text"]:
        raise StepFailed("homepage_load", "首頁無法載入或缺少線上投保標題", homepage, steps)

    try:
        quote = http_request(
            "POST",
            f"{base_url}/api/quote",
            timeout_ms,
            {"product": "travel", "age": 30, "coverage": 1_000_000, "test_user": "TEST-USER-001"},
        )
    except StepFailed as exc:
        raise StepFailed("quote_api", exc.message, exc.evidence, steps)
    steps.append({"name": "quote_api", **summarize_response(quote)})
    if not quote["ok"]:
        raise StepFailed("quote_api", f"報價 API 回傳 HTTP {quote['status_code']}", quote, steps)
    if not quote["json"] or "quote_id" not in quote["json"]:
        raise StepFailed("quote_api", "報價 API 未回傳 quote_id", quote, steps)

    try:
        preview = http_request(
            "POST",
            f"{base_url}/api/application/preview",
            timeout_ms,
            {"quote_id": quote["json"]["quote_id"], "mode": "preview_only"},
        )
    except StepFailed as exc:
        raise StepFailed("application_preview", exc.message, exc.evidence, steps)
    steps.append({"name": "application_preview", **summarize_response(preview)})
    if not preview["ok"]:
        raise StepFailed("application_preview", f"付款前確認回傳 HTTP {preview['status_code']}", preview, steps)
    if preview["json"].get("policy_issued") or preview["json"].get("payment_charged"):
        raise StepFailed("application_preview", "測試流程不應付款或出單", preview, steps)

    try:
        frontend_errors = http_request("GET", f"{base_url}/api/client-errors", timeout_ms)
    except StepFailed as exc:
        raise StepFailed("frontend_error_check", exc.message, exc.evidence, steps)
    steps.append({"name": "frontend_error_check", **summarize_response(frontend_errors)})
    errors = (frontend_errors["json"] or {}).get("errors", [])
    if errors:
        raise StepFailed("frontend_error_check", "偵測到前端錯誤", frontend_errors, steps)

    return steps


def summarize_response(response: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": response["ok"],
        "status_code": response["status_code"],
        "duration_ms": response["duration_ms"],
        "content_type": response["content_type"],
        "body_excerpt": response["body_text"][:260],
    }


def classify_failure(step: str, evidence: dict[str, Any]) -> dict[str, str]:
    if step in {"network_timeout", "application_preview"} and "timed out" in json.dumps(evidence):
        return {
            "category": "timeout",
            "likely_owner": "application_or_downstream_dependency",
            "recommended_action": "先檢查付款前確認或下游服務延遲，保留該 step 的 request timestamp 與 timeout threshold。",
        }
    if step == "quote_api":
        return {
            "category": "api_5xx_or_quote_engine_failure",
            "likely_owner": "quote_service",
            "recommended_action": "檢查報價服務健康、最近部署與錯誤率；若正式化可接 CloudWatch Alarm 與 runbook。",
        }
    if step == "frontend_error_check":
        return {
            "category": "frontend_runtime_error",
            "likely_owner": "web_frontend",
            "recommended_action": "保留 console error、release version 與頁面路徑；回查前端 bundle 或資料契約變更。",
        }
    if step == "homepage_load":
        return {
            "category": "site_availability_or_content_regression",
            "likely_owner": "web_edge_or_frontend",
            "recommended_action": "檢查入口頁可用性、DNS/CDN/ALB 與首頁內容回歸。",
        }
    return {
        "category": "unknown",
        "likely_owner": "triage_required",
        "recommended_action": "先根據 failed step、HTTP status、duration 與 body excerpt 進行人工判讀。",
    }


def write_outputs(out_dir: Path, result: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "latest-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "latest-report.md").write_text(render_markdown_report(result), encoding="utf-8")

    if result["status"] == "FAIL":
        safe_run_id = result["run_id"].replace(":", "").replace(".", "-")
        packet_name = f"incident-packet-{safe_run_id}.json"
        (out_dir / packet_name).write_text(json.dumps(result["incident_packet"], ensure_ascii=False, indent=2), encoding="utf-8")


def render_markdown_report(result: dict[str, Any]) -> str:
    lines = [
        f"# 線上投保穩定性 Canary 報告",
        "",
        f"- Run ID：`{result['run_id']}`",
        f"- 情境：`{result['scenario_label']}`",
        f"- 狀態：`{result['status']}`",
        f"- Base URL：`{result['base_url']}`",
        f"- Timeout：`{result['timeout_ms']} ms`",
        "",
        "## 步驟結果",
        "",
        "| Step | OK | HTTP | Duration ms |",
        "|---|---:|---:|---:|",
    ]
    for step in result["steps"]:
        lines.append(f"| `{step['name']}` | {step['ok']} | {step['status_code']} | {step['duration_ms']} |")

    if result["status"] == "FAIL":
        incident = result["incident_packet"]
        lines.extend(
            [
                "",
                "## Incident Packet",
                "",
                f"- Failed step：`{incident['failed_step']}`",
                f"- Failure category：`{incident['classification']['category']}`",
                f"- Likely owner：`{incident['classification']['likely_owner']}`",
                f"- Recommended action：{incident['classification']['recommended_action']}",
                "",
                "## 驗證限制",
                "",
                "- 此結果來自本機 mock PoC，不代表公司真實系統狀態。",
                "- 測試資料為假資料，不付款、不出單、不使用客戶個資。",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    run_id = now_iso()
    result: dict[str, Any] = {
        "run_id": run_id,
        "base_url": args.base_url.rstrip("/"),
        "scenario_label": args.scenario_label,
        "timeout_ms": args.timeout_ms,
        "status": "PASS",
        "steps": [],
        "started_at": run_id,
    }

    try:
        result["steps"] = run_flow(result["base_url"], args.timeout_ms)
    except StepFailed as exc:
        result["status"] = "FAIL"
        result["steps"] = exc.steps
        result["failed_step"] = exc.step
        result["failure_message"] = exc.message
        result["incident_packet"] = {
            "run_id": run_id,
            "scenario_label": args.scenario_label,
            "failed_step": exc.step,
            "message": exc.message,
            "classification": classify_failure(exc.step, exc.evidence),
            "evidence": exc.evidence,
            "privacy_note": "mock data only; no customer PII, no payment, no policy issuance",
        }

    result["finished_at"] = now_iso()
    write_outputs(Path(args.out), result)
    print(f"status={result['status']} run_id={run_id} report={Path(args.out) / 'latest-report.md'}")
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
