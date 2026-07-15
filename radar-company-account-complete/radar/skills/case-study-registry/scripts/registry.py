# -*- coding: utf-8 -*-
"""Manage enterprise case-study JSON files.

Examples:
  python registry.py list --cases ../tech-intel-scan/data/case_studies
  python registry.py search --cases ../tech-intel-scan/data/case_studies --tag bedrock
  python registry.py add --cases ../tech-intel-scan/data/case_studies --id demo --customer "Demo Co" --tags bedrock,rag --score 4
"""
import argparse
import json
from pathlib import Path


def load_cases(cases_dir):
    cases = []
    for path in sorted(Path(cases_dir).glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data["_path"] = str(path)
        cases.append(data)
    return cases


def cmd_list(args):
    for case in load_cases(args.cases):
        score = case.get("relevance_to_cathay", {}).get("score", "?")
        print(f"{case.get('id')} | {case.get('customer')} | Cathay relevance {score}/5")


def cmd_search(args):
    query = args.tag.lower()
    for case in load_cases(args.cases):
        tags = [t.lower() for t in case.get("matched_technologies", []) + case.get("industry_tags", [])]
        if query in tags:
            print(f"{case.get('id')} | {case.get('customer')} | {case['_path']}")


def cmd_add(args):
    cases_dir = Path(args.cases)
    cases_dir.mkdir(parents=True, exist_ok=True)
    item = {
        "id": args.id,
        "customer": args.customer,
        "industry_tags": [t.strip() for t in args.industry.split(",") if t.strip()],
        "region": args.region,
        "year": args.year,
        "system": args.system,
        "partner": args.partner,
        "aws_services": [t.strip() for t in args.services.split(",") if t.strip()],
        "matched_technologies": [t.strip() for t in args.tags.split(",") if t.strip()],
        "approach": args.approach,
        "outcomes": [args.outcome],
        "compliance_signals": [],
        "relevance_to_cathay": {"score": args.score, "reason": args.reason},
        "source": args.source,
        "key_takeaways": [],
    }
    out = cases_dir / f"{args.id}.json"
    out.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("list")
    p.add_argument("--cases", required=True)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("search")
    p.add_argument("--cases", required=True)
    p.add_argument("--tag", required=True)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("add")
    p.add_argument("--cases", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--customer", required=True)
    p.add_argument("--tags", required=True)
    p.add_argument("--score", type=int, required=True)
    p.add_argument("--reason", default="")
    p.add_argument("--industry", default="")
    p.add_argument("--region", default="")
    p.add_argument("--year", type=int, default=2026)
    p.add_argument("--system", default="")
    p.add_argument("--partner", default="")
    p.add_argument("--services", default="")
    p.add_argument("--approach", default="")
    p.add_argument("--outcome", default="")
    p.add_argument("--source", default="")
    p.set_defaults(func=cmd_add)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
