"""Command line tools for the radar redesign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .s1 import build_direct_url_scan, build_scan
from .s2 import build_compare


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


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
