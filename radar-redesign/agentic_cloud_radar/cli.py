"""Command line tools for the radar redesign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .s0 import build_demand_card


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentic-cloud-radar")
    subparsers = parser.add_subparsers(dest="command", required=True)

    s0_parser = subparsers.add_parser("s0", help="Build and validate an S0 demand card.")
    s0_parser.add_argument("--input", required=True, help="Path to an S0 input JSON file.")
    s0_parser.add_argument("--output", help="Optional path for the normalized demand card.")

    args = parser.parse_args(argv)
    if args.command == "s0":
        return _run_s0(Path(args.input), Path(args.output) if args.output else None)
    parser.error("unknown command")
    return 2


def _run_s0(input_path: Path, output_path: Path | None) -> int:
    with input_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    result = build_demand_card(raw).to_dict()
    payload = json.dumps(result, ensure_ascii=False, indent=2)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    if result["status"] in {"blocked_sensitive", "needs_revision"}:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
