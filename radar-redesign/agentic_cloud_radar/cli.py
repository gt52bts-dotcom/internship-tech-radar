"""Command line tools for the radar redesign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .s1 import build_direct_url_scan, build_scan
from .s2 import build_compare
from .s3 import build_evaluate
from .s4 import build_validate
from .s4_deployer import DeploymentError, build_deployment_context, execute_cleanup, execute_deployment, record_console_review
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

    s3_parser = subparsers.add_parser("s3", help="Evaluate a human-shortlisted set of S2 proposal cards.")
    s3_parser.add_argument("--input", required=True, help="Path to an S2 comparison artifact JSON file.")
    s3_parser.add_argument("--shortlist", help="Optional path to a human shortlist request JSON file.")
    s3_parser.add_argument("--output", help="Optional path for the S3 evaluation artifact.")

    s4_parser = subparsers.add_parser("s4", help="Validate S3 results without automatically starting cloud resources.")
    s4_parser.add_argument("--input", required=True, help="Path to an S3 evaluation artifact JSON file.")
    s4_parser.add_argument("--approval", help="Optional path to an S4 approval request JSON file.")
    s4_parser.add_argument("--output", help="Optional path for the S4 validation artifact.")

    deploy_parser = subparsers.add_parser("s4-deploy", help="Build or explicitly execute a human-approved, candidate-specific S4 PoC.")
    deploy_parser.add_argument("--input", required=True, help="Path to an S3 evaluation artifact JSON file.")
    deploy_parser.add_argument("--approval", required=True, help="Path to a human S4 deployment approval JSON file.")
    deploy_parser.add_argument("--output", required=True, help="Path for the S4 deployment context JSON file.")
    deploy_parser.add_argument("--execute", action="store_true", help="Actually create AWS resources after all approval checks pass.")
    deploy_parser.add_argument("--runtime-output", help="Required with --execute; path for S4 runtime evidence JSON.")

    console_parser = subparsers.add_parser("s4-console-review", help="Record required human AWS Console verification before cleanup.")
    console_parser.add_argument("--input", required=True, help="Path to an S4 runtime evidence JSON file.")
    console_parser.add_argument("--confirmed-by", required=True, help="Named human who completed the Console review.")
    console_parser.add_argument("--notes", help="Optional concise Console review note.")
    console_parser.add_argument("--output", required=True, help="Path for the Console-reviewed S4 runtime JSON file.")

    cleanup_parser = subparsers.add_parser("s4-cleanup", help="Explicitly remove a Console-reviewed S4 PoC and record cleanup evidence.")
    cleanup_parser.add_argument("--input", required=True, help="Path to a Console-reviewed S4 runtime JSON file.")
    cleanup_parser.add_argument("--execute", action="store_true", help="Actually delete only the reviewed PoC stack and its test data.")
    cleanup_parser.add_argument("--output", required=True, help="Path for the cleanup-complete S4 runtime JSON file.")

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
        )
    if args.command == "s4":
        return _run_s4(
            Path(args.input),
            Path(args.approval) if args.approval else None,
            Path(args.output) if args.output else None,
        )
    if args.command == "s4-deploy":
        return _run_s4_deploy(
            Path(args.input), Path(args.approval), Path(args.output), args.execute,
            Path(args.runtime_output) if args.runtime_output else None,
        )
    if args.command == "s4-console-review":
        return _run_s4_console_review(Path(args.input), args.confirmed_by, args.notes, Path(args.output))
    if args.command == "s4-cleanup":
        return _run_s4_cleanup(Path(args.input), args.execute, Path(args.output))
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


def _run_s3(input_path: Path, shortlist_path: Path | None, output_path: Path | None) -> int:
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


def _run_s4_deploy(
    input_path: Path, approval_path: Path, output_path: Path, execute: bool, runtime_output: Path | None
) -> int:
    if execute and runtime_output is None:
        raise SystemExit("s4-deploy --execute requires --runtime-output.")
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
        print(str(exc), file=sys.stderr)
        return 1


def _run_s4_console_review(input_path: Path, confirmed_by: str, notes: str | None, output_path: Path) -> int:
    try:
        _write_json(output_path, record_console_review(_read_json(input_path), confirmed_by, notes))
        return 0
    except DeploymentError as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _run_s4_cleanup(input_path: Path, execute: bool, output_path: Path) -> int:
    if not execute:
        print("s4-cleanup only creates or deletes resources when --execute is explicitly supplied.", file=sys.stderr)
        return 1
    try:
        _write_json(output_path, execute_cleanup(_read_json(input_path)))
        return 0
    except DeploymentError as exc:
        print(str(exc), file=sys.stderr)
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


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _write_json(path: Path | None, value: dict) -> None:
    if path is None:
        raise ValueError("An output path is required.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
