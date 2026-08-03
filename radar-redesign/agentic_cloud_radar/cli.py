"""Command line tools for the radar redesign."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from .s1 import build_direct_url_scan, build_scan
from .s2 import build_compare
from .s3 import build_evaluate, render_poc_decision_report, render_poc_decision_report_html
from .s4 import build_validate
from .s4_deployer import (
    DeploymentError,
    build_approval_template,
    build_console_review_packet,
    build_deployment_context,
    execute_abort_cleanup,
    execute_cleanup,
    execute_deployment,
    record_console_review,
)
from .s5 import build_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentic-cloud-radar")
    subparsers = parser.add_subparsers(dest="command", required=True)

    s1_parser = subparsers.add_parser("s1", help="Discover public technology candidates through AWS RSS and GitHub public search.")
    s1_parser.add_argument("--input", required=True, help="Path to an optional S1 discovery request JSON file.")
    s1_parser.add_argument("--output", help="Optional path for the S1 scan artifact.")

    s1_url_parser = subparsers.add_parser(
        "s1-url",
        help="Import one user-supplied trusted public URL directly into an S1 artifact (no S0 required).",
    )
    s1_url_parser.add_argument("--url", required=True, help="AWS, GitHub, GitLab, or Codeberg HTTPS page to import.")
    s1_url_parser.add_argument("--output", help="Optional path for the S1 direct-import artifact.")

    s2_parser = subparsers.add_parser("s2", help="Build an S2 comparison artifact from an S1 scan artifact.")
    s2_parser.add_argument("--input", required=True, help="Path to an S1 scan artifact JSON file.")
    s2_parser.add_argument("--output", help="Optional path for the S2 comparison artifact.")

    s3_parser = subparsers.add_parser("s3", help="Evaluate and quote S2 proposal cards before the merged PoC decision gate.")
    s3_parser.add_argument("--input", required=True, help="Path to an S2 comparison artifact JSON file.")
    s3_parser.add_argument("--shortlist", help="Optional candidate filter JSON file; this is not a PoC approval gate.")
    s3_parser.add_argument("--output", help="Optional path for the S3 evaluation artifact.")
    s3_parser.add_argument("--decision-report-output", help="Optional path for the human-readable Skill 3 PoC decision report.")
    s3_parser.add_argument("--decision-report-html-output", help="Optional path for the human-facing Skill 3 PoC decision report HTML.")
    s3_parser.add_argument("--decision-report-image", help="Optional PNG/JPG architecture image to embed into the HTML report.")

    s4_parser = subparsers.add_parser("s4", help="Validate S3 results without automatically starting cloud resources.")
    s4_parser.add_argument("--input", required=True, help="Path to an S3 evaluation artifact JSON file.")
    s4_parser.add_argument("--approval", help="Optional path to an S4 approval request JSON file.")
    s4_parser.add_argument("--output", help="Optional path for the S4 validation artifact.")

    approval_parser = subparsers.add_parser(
        "s4-approval-template",
        help="Create a human-editable S4 deployment approval JSON file from one Skill 3 candidate.",
    )
    approval_parser.add_argument("--input", required=True, help="Path to an S3 evaluation artifact JSON file.")
    approval_parser.add_argument("--selected-candidate-id", help="Candidate ID to approve; optional when Skill 3 has exactly one PoC candidate.")
    approval_parser.add_argument("--approved-by", help="Named human approver to prefill.")
    approval_parser.add_argument("--authorize", action="store_true", help="Write deployment_authorized=true after the named human has approved.")
    approval_parser.add_argument("--output", required=True, help="Path for the S4 approval JSON file.")

    deploy_parser = subparsers.add_parser("s4-deploy", help="Build or explicitly execute a human-approved, candidate-specific S4 PoC.")
    deploy_parser.add_argument("--input", required=True, help="Path to an S3 evaluation artifact JSON file.")
    deploy_parser.add_argument("--approval", required=True, help="Path to a human S4 deployment approval JSON file.")
    deploy_parser.add_argument("--output", required=True, help="Path for the S4 deployment context JSON file.")
    deploy_parser.add_argument("--execute", action="store_true", help="Actually create AWS resources after all approval checks pass.")
    deploy_parser.add_argument("--runtime-output", help="Required with --execute; path for S4 runtime evidence JSON.")

    packet_parser = subparsers.add_parser(
        "s4-console-review-packet",
        help="Create the Infrastructure Composer screenshot and human-confirmation checklist for one deployed PoC.",
    )
    packet_parser.add_argument("--input", required=True, help="Path to an S4 runtime evidence JSON awaiting Console review.")
    packet_parser.add_argument(
        "--review-timeout-minutes",
        type=int,
        default=60,
        help="Minutes a screenshot review may wait before a cost-control abort is allowed (default: 60).",
    )
    packet_parser.add_argument("--output", required=True, help="Path for the human-facing Console review packet JSON file.")

    console_parser = subparsers.add_parser("s4-console-review", help="Record screenshot-backed human AWS Console verification before cleanup.")
    console_parser.add_argument("--input", required=True, help="Path to an S4 runtime evidence JSON file.")
    console_parser.add_argument("--packet", required=True, help="Path to the Console review packet that defined required screenshots.")
    console_parser.add_argument("--review-evidence", required=True, help="Path to Console screenshot evidence JSON from the review packet.")
    console_parser.add_argument("--confirmed-by", required=True, help="Named human who completed the Console review.")
    console_parser.add_argument("--shared-via", required=True, choices=["gui", "conversation"], help="Where the human actually saw the screenshot.")
    console_parser.add_argument("--notes", help="Optional concise Console review note.")
    console_parser.add_argument("--output", required=True, help="Path for the Console-reviewed S4 runtime JSON file.")

    cleanup_parser = subparsers.add_parser("s4-cleanup", help="Explicitly remove a Console-reviewed S4 PoC and record cleanup evidence.")
    cleanup_parser.add_argument("--input", required=True, help="Path to a Console-reviewed S4 runtime JSON file.")
    cleanup_parser.add_argument("--execute", action="store_true", help="Actually delete only the reviewed PoC stack and its test data.")
    cleanup_parser.add_argument("--output", required=True, help="Path for the cleanup-complete S4 runtime JSON file.")
    cleanup_parser.add_argument("--usage-snapshot-output", help="Optional path for pre_cleanup_usage_snapshot.json.")

    close_parser = subparsers.add_parser(
        "s4-close",
        help="After screenshot-backed human confirmation, automatically clean only this PoC run and record verification.",
    )
    close_parser.add_argument("--input", required=True, help="Path to an S4 runtime evidence JSON awaiting Console review.")
    close_parser.add_argument("--packet", required=True, help="Path to the Console review packet that defined required screenshots.")
    close_parser.add_argument("--review-evidence", required=True, help="Path to Console screenshot evidence JSON from the review packet.")
    close_parser.add_argument("--confirmed-by", required=True, help="Named human who approved cleanup after seeing the screenshots.")
    close_parser.add_argument("--shared-via", required=True, choices=["gui", "conversation"], help="Where the human actually saw the screenshot.")
    close_parser.add_argument("--notes", help="Optional concise Console review note.")
    close_parser.add_argument("--execute", action="store_true", help="Actually clean the reviewed run after the explicit human confirmation.")
    close_parser.add_argument("--output", required=True, help="Path for the cleanup-verified S4 runtime JSON file.")
    close_parser.add_argument("--usage-snapshot-output", help="Optional path for pre_cleanup_usage_snapshot.json.")

    abort_parser = subparsers.add_parser(
        "s4-abort",
        help="Emergency cleanup for a timed-out or failed S4 PoC without treating it as a normal Console-reviewed close.",
    )
    abort_parser.add_argument("--input", required=True, help="Path to an S4 runtime JSON file.")
    abort_parser.add_argument("--packet", help="Required for a review-timeout abort; omit only after deployment or close failure.")
    abort_parser.add_argument("--confirmed-by", required=True, help="Named human approving emergency cost-control cleanup.")
    abort_parser.add_argument("--reason", required=True, help="Why the normal Console review path is being skipped.")
    abort_parser.add_argument("--execute", action="store_true", help="Actually delete only the run-derived PoC stack and test data.")
    abort_parser.add_argument("--output", required=True, help="Path for the abort-cleanup S4 runtime JSON file.")
    abort_parser.add_argument("--usage-snapshot-output", help="Optional path for pre_cleanup_usage_snapshot.json.")

    s5_parser = subparsers.add_parser("s5", help="Render a source-bound JSON and Markdown report from S1-S4 artifacts.")
    s5_parser.add_argument("--s1", required=True, help="Path to an S1 scan artifact JSON file.")
    s5_parser.add_argument("--s2", help="Path to an S2 comparison artifact JSON file.")
    s5_parser.add_argument("--s3", help="Path to a Skill 3 evaluation artifact JSON file.")
    s5_parser.add_argument("--s4", help="Path to an S4 validation artifact JSON file.")
    s5_parser.add_argument("--runtime", help="Optional path to S4 runtime evidence JSON file.")
    s5_parser.add_argument("--output", required=True, help="Path for the Skill 5 JSON report artifact.")
    s5_parser.add_argument("--markdown-output", help="Optional path for the rendered Markdown report.")

    args = parser.parse_args(argv)
    if args.command == "s1":
        return _run_s1(
            Path(args.input),
            Path(args.output) if args.output else None,
        )
    if args.command == "s1-url":
        return _run_s1_url(args.url, Path(args.output) if args.output else None)
    if args.command == "s2":
        return _run_s2(Path(args.input), Path(args.output) if args.output else None)
    if args.command == "s3":
        return _run_s3(
            Path(args.input),
            Path(args.shortlist) if args.shortlist else None,
            Path(args.output) if args.output else None,
            Path(args.decision_report_output) if args.decision_report_output else None,
            Path(args.decision_report_html_output) if args.decision_report_html_output else None,
            Path(args.decision_report_image) if args.decision_report_image else None,
        )
    if args.command == "s4":
        return _run_s4(
            Path(args.input),
            Path(args.approval) if args.approval else None,
            Path(args.output) if args.output else None,
        )
    if args.command == "s4-approval-template":
        return _run_s4_approval_template(
            Path(args.input),
            args.selected_candidate_id,
            args.approved_by,
            args.authorize,
            Path(args.output),
        )
    if args.command == "s4-deploy":
        return _run_s4_deploy(
            Path(args.input), Path(args.approval), Path(args.output), args.execute,
            Path(args.runtime_output) if args.runtime_output else None,
        )
    if args.command == "s4-console-review-packet":
        return _run_s4_console_review_packet(Path(args.input), args.review_timeout_minutes, Path(args.output))
    if args.command == "s4-console-review":
        return _run_s4_console_review(
            Path(args.input), Path(args.packet), Path(args.review_evidence), args.confirmed_by, args.shared_via, args.notes, Path(args.output)
        )
    if args.command == "s4-cleanup":
        return _run_s4_cleanup(Path(args.input), args.execute, Path(args.output), Path(args.usage_snapshot_output) if args.usage_snapshot_output else None)
    if args.command == "s4-close":
        return _run_s4_close(
            Path(args.input), Path(args.packet), Path(args.review_evidence), args.confirmed_by, args.shared_via, args.notes, args.execute, Path(args.output),
            Path(args.usage_snapshot_output) if args.usage_snapshot_output else None,
        )
    if args.command == "s4-abort":
        return _run_s4_abort(
            Path(args.input), Path(args.packet) if args.packet else None, args.confirmed_by, args.reason, args.execute, Path(args.output),
            Path(args.usage_snapshot_output) if args.usage_snapshot_output else None,
        )
    if args.command == "s5":
        return _run_s5(
            Path(args.s1),
            Path(args.s2) if args.s2 else None,
            Path(args.s3) if args.s3 else None,
            Path(args.s4) if args.s4 else None,
            Path(args.runtime) if args.runtime else None,
            Path(args.output),
            Path(args.markdown_output) if args.markdown_output else None,
        )
    parser.error("unknown command")
    return 2


def _run_s1(
    input_path: Path,
    output_path: Path | None,
) -> int:
    with input_path.open("r", encoding="utf-8-sig") as handle:
        discovery_request = json.load(handle)

    result = build_scan(discovery_request).to_dict()
    payload = json.dumps(result, ensure_ascii=False, indent=2)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    if result["status"] in {"blocked_s0_not_confirmed", "needs_revision", "no_candidates"}:
        return 1
    return 0


def _run_s1_url(requested_url: str, output_path: Path | None) -> int:
    result = build_direct_url_scan(requested_url).to_dict()
    payload = json.dumps(result, ensure_ascii=False, indent=2)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    if result["status"] in {"needs_revision", "no_candidates"}:
        return 1
    return 0


def _run_s2(input_path: Path, output_path: Path | None) -> int:
    with input_path.open("r", encoding="utf-8-sig") as handle:
        scan = json.load(handle)

    result = build_compare(scan).to_dict()
    payload = json.dumps(result, ensure_ascii=False, indent=2)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    if result["status"] in {"blocked_s1_not_usable", "needs_revision", "no_comparable_candidates"}:
        return 1
    return 0


def _run_s3(
    input_path: Path,
    shortlist_path: Path | None,
    output_path: Path | None,
    decision_report_path: Path | None,
    decision_report_html_path: Path | None,
    decision_report_image_path: Path | None,
) -> int:
    with input_path.open("r", encoding="utf-8-sig") as handle:
        compare = json.load(handle)
    shortlist = None
    if shortlist_path:
        with shortlist_path.open("r", encoding="utf-8-sig") as handle:
            shortlist = json.load(handle)

    result = build_evaluate(compare, shortlist).to_dict()
    payload = json.dumps(result, ensure_ascii=False, indent=2)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if decision_report_path:
        decision_report_path.parent.mkdir(parents=True, exist_ok=True)
        decision_report_path.write_text(render_poc_decision_report(result), encoding="utf-8")
    if decision_report_html_path:
        decision_report_html_path.parent.mkdir(parents=True, exist_ok=True)
        decision_report_html_path.write_text(
            render_poc_decision_report_html(result, decision_report_image_path),
            encoding="utf-8",
        )

    if result["status"] in {"blocked_s2_not_usable", "needs_revision"}:
        return 1
    return 0


def _run_s4(input_path: Path, approval_path: Path | None, output_path: Path | None) -> int:
    with input_path.open("r", encoding="utf-8-sig") as handle:
        evaluate = json.load(handle)
    approval = None
    if approval_path:
        with approval_path.open("r", encoding="utf-8-sig") as handle:
            approval = json.load(handle)

    result = build_validate(evaluate, approval).to_dict()
    payload = json.dumps(result, ensure_ascii=False, indent=2)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    if result["status"] in {"blocked_s3_not_usable", "needs_revision"}:
        return 1
    return 0


def _run_s4_approval_template(
    input_path: Path,
    selected_candidate_id: str | None,
    approved_by: str | None,
    authorize: bool,
    output_path: Path,
) -> int:
    try:
        approval = build_approval_template(_read_json(input_path), selected_candidate_id, approved_by, authorize)
        _write_json(output_path, approval)
        return 0
    except DeploymentError as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _run_s4_deploy(
    input_path: Path, approval_path: Path, output_path: Path, execute: bool, runtime_output: Path | None
) -> int:
    if execute and runtime_output is None:
        raise SystemExit("s4-deploy --execute requires --runtime-output.")
    context = None
    evaluate = _read_json(input_path)
    approval = _read_json(approval_path)
    try:
        context = build_deployment_context(evaluate, approval)
        _write_json(output_path, context)
        if not execute:
            return 0 if context["status"] == "ready_for_manual_deployment" else 1
        runtime = execute_deployment(context)
        _write_json(runtime_output, runtime)
        return 0
    except DeploymentError as exc:
        if execute and runtime_output is not None and context is not None:
            _write_json(runtime_output, _deployment_failed_runtime(context, exc))
        print(str(exc), file=sys.stderr)
        return 1


def _run_s4_console_review_packet(input_path: Path, review_timeout_minutes: int, output_path: Path) -> int:
    try:
        _write_json(output_path, build_console_review_packet(_read_json(input_path), review_timeout_minutes))
        return 0
    except DeploymentError as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _run_s4_console_review(
    input_path: Path,
    packet_path: Path,
    evidence_path: Path,
    confirmed_by: str,
    shared_via: str,
    notes: str | None,
    output_path: Path,
) -> int:
    try:
        _write_json(
            output_path,
            record_console_review(
                _read_json(input_path),
                confirmed_by,
                notes,
                _read_json(evidence_path),
                _read_json(packet_path),
                shared_via,
            ),
        )
        return 0
    except DeploymentError as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _run_s4_cleanup(input_path: Path, execute: bool, output_path: Path, usage_snapshot_path: Path | None) -> int:
    if not execute:
        print("s4-cleanup only creates or deletes resources when --execute is explicitly supplied.", file=sys.stderr)
        return 1
    try:
        result = execute_cleanup(_read_json(input_path))
        _write_json(output_path, result)
        _write_usage_snapshot_if_requested(usage_snapshot_path, result)
        return 0
    except DeploymentError as exc:
        _write_runtime_failure_if_present(output_path, exc)
        return 1


def _run_s4_close(
    input_path: Path,
    packet_path: Path,
    evidence_path: Path,
    confirmed_by: str,
    shared_via: str,
    notes: str | None,
    execute: bool,
    output_path: Path,
    usage_snapshot_path: Path | None,
) -> int:
    if not execute:
        print("s4-close only deletes resources when --execute is explicitly supplied after human screenshot confirmation.", file=sys.stderr)
        return 1
    try:
        reviewed = record_console_review(
            _read_json(input_path), confirmed_by, notes, _read_json(evidence_path), _read_json(packet_path), shared_via
        )
        result = execute_cleanup(reviewed)
        _write_json(output_path, result)
        _write_usage_snapshot_if_requested(usage_snapshot_path, result)
        return 0
    except DeploymentError as exc:
        _write_runtime_failure_if_present(output_path, exc)
        return 1


def _run_s4_abort(
    input_path: Path,
    packet_path: Path | None,
    confirmed_by: str,
    reason: str,
    execute: bool,
    output_path: Path,
    usage_snapshot_path: Path | None,
) -> int:
    if not execute:
        print("s4-abort only deletes resources when --execute is explicitly supplied by a named approver.", file=sys.stderr)
        return 1
    try:
        result = execute_abort_cleanup(_read_json(input_path), confirmed_by, reason, _read_json(packet_path) if packet_path else None)
        _write_json(output_path, result)
        _write_usage_snapshot_if_requested(usage_snapshot_path, result)
        return 0
    except DeploymentError as exc:
        _write_runtime_failure_if_present(output_path, exc)
        return 1


def _run_s5(
    s1_path: Path,
    s2_path: Path | None,
    s3_path: Path | None,
    s4_path: Path | None,
    runtime_path: Path | None,
    output_path: Path,
    markdown_path: Path | None,
) -> int:
    report = build_report(
        _read_json(s1_path),
        _read_json(s2_path) if s2_path else None,
        _read_json(s3_path) if s3_path else None,
        _read_json(s4_path) if s4_path else None,
        _read_json(runtime_path) if runtime_path else None,
    )
    _write_json(output_path, report)
    if markdown_path:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(report["markdown"], encoding="utf-8")
    return 0 if report["status"] != "incomplete_artifacts" else 1


def _write_runtime_failure_if_present(output_path: Path, exc: DeploymentError) -> None:
    message = str(exc)
    try:
        payload = json.loads(message)
    except json.JSONDecodeError:
        print(message, file=sys.stderr)
        return
    if isinstance(payload, dict) and payload.get("stage") == "S4":
        _write_json(output_path, payload)
    print(message, file=sys.stderr)


def _deployment_failed_runtime(context: dict, exc: DeploymentError) -> dict:
    return {
        "schema_version": "s4.runtime-evidence.v3",
        "stage": "S4",
        "run_id": context.get("run_id"),
        "status": "deployment_failed",
        "failed_at": datetime.now(timezone.utc).isoformat(),
        "lineage": context.get("lineage"),
        "deployment": {
            **dict(context.get("deployment") or {}),
            "deployment_method": "CDK synth followed by CloudFormation create-stack",
            "stack_status": "failed_or_unknown",
        },
        "verification": {"status": "not_verified_due_to_deployment_failure"},
        "console_review": {
            "status": "not_available",
            "evidence_status": "not_captured_deployment_failed",
        },
        "cleanup": {
            "status": "pending_abort_cleanup",
            "reason": "Deployment failed before normal Console review could be completed.",
        },
        "error": str(exc),
    }


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _write_json(path: Path | None, value: dict) -> None:
    if path is None:
        raise ValueError("An output path is required.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_usage_snapshot_if_requested(path: Path | None, runtime: dict) -> None:
    if path is None:
        return
    snapshot = runtime.get("pre_cleanup_usage_snapshot") or {
        "schema_version": "s4.pre-cleanup-usage-snapshot.v1",
        "status": "not_recorded",
        "rule": "No pre-cleanup usage snapshot was present in the runtime artifact.",
    }
    _write_json(path, snapshot)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
