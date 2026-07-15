# -*- coding: utf-8 -*-
"""Record and summarize human picks for the AI-vs-human experiment.

Examples:
  python tracker.py record --log data/picks.jsonl --run-id demo --mode blind --pick A03 --minutes 12
  python tracker.py summary --log data/picks.jsonl
"""
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def read_log(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def cmd_record(args):
    path = Path(args.log)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "time": datetime.now(timezone.utc).isoformat(),
        "run_id": args.run_id,
        "mode": args.mode,
        "pick": args.pick,
        "minutes": args.minutes,
        "notes": args.notes,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"recorded {args.pick} for {args.run_id}")


def cmd_summary(args):
    rows = read_log(args.log)
    by_mode = Counter(row["mode"] for row in rows)
    by_pick = Counter(row["pick"] for row in rows)
    minutes = [float(row.get("minutes", 0)) for row in rows if row.get("minutes") is not None]
    avg_minutes = round(sum(minutes) / len(minutes), 2) if minutes else 0
    print(json.dumps({
        "records": len(rows),
        "by_mode": dict(by_mode),
        "by_pick": dict(by_pick),
        "average_minutes": avg_minutes,
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("record")
    p.add_argument("--log", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--mode", choices=["blind", "assisted"], required=True)
    p.add_argument("--pick", required=True)
    p.add_argument("--minutes", type=float, default=0)
    p.add_argument("--notes", default="")
    p.set_defaults(func=cmd_record)

    p = sub.add_parser("summary")
    p.add_argument("--log", required=True)
    p.set_defaults(func=cmd_summary)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
