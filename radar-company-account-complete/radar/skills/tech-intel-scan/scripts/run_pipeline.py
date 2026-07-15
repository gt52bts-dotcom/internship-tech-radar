# -*- coding: utf-8 -*-
"""Run the local five-step tech-intel pipeline.

Examples:
  python run_pipeline.py --run-id demo --use-fixtures --offline
  python run_pipeline.py --run-id today
"""
import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
DEFAULT_OUT = SCRIPT_DIR.parent / "out"


def run(cmd, label):
    print(f"\n=== {label} ===")
    result = subprocess.run(cmd, cwd=SCRIPT_DIR)
    if result.returncode != 0:
        print(f"[FAIL] {label}", file=sys.stderr)
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=datetime.now().strftime("%Y%m%d-%H%M"))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--use-fixtures", action="store_true")
    parser.add_argument("--offline", action="store_true", help="Do not call Anthropic API")
    parser.add_argument("--evaluator", default="claude-sonnet-4-5")
    parser.add_argument("--validator", default="claude-haiku-4-5")
    args = parser.parse_args()

    py = sys.executable
    out_dir = Path(args.out) / "runs" / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Run ID: {args.run_id}")
    print(f"Output directory: {out_dir}")

    cmd = [
        py,
        "rss_fetcher.py",
        "--output",
        str(out_dir / "s1_scan.json"),
        "--fixtures",
        str(DATA_DIR / "fixtures.json"),
    ]
    if args.use_fixtures:
        cmd.append("--use-fixtures")
    else:
        cmd.extend(["--sources", str(DATA_DIR / "sources.json")])
    run(cmd, "Step 1: scan RSS/fixtures and L0 filter")

    run(
        [
            py,
            "rank.py",
            "--input",
            str(out_dir / "s1_scan.json"),
            "--output",
            str(out_dir / "s2_compare.json"),
        ],
        "Step 2: compare and L1 rank",
    )

    cmd = [
        py,
        "evaluate.py",
        "--input",
        str(out_dir / "s2_compare.json"),
        "--cases",
        str(DATA_DIR / "case_studies"),
        "--output",
        str(out_dir / "s3_evaluate.json"),
        "--model",
        args.evaluator,
    ]
    if args.offline:
        cmd.append("--offline")
    run(cmd, "Step 3: evaluate candidates")

    cmd = [
        py,
        "validate.py",
        "--input",
        str(out_dir / "s3_evaluate.json"),
        "--output",
        str(out_dir / "s4_validate.json"),
        "--model",
        args.validator,
    ]
    if args.offline:
        cmd.append("--offline")
    run(cmd, "Step 4: validate independently")

    run(
        [
            py,
            "report.py",
            "--run-dir",
            str(out_dir),
            "--output",
            str(out_dir / "report.html"),
            "--run-id",
            args.run_id,
        ],
        "Step 5: generate report",
    )

    print("\n" + "=" * 40)
    print("  Pipeline completed")
    print(f"  Report: {out_dir / 'report.html'}")
    print("=" * 40)


if __name__ == "__main__":
    main()
