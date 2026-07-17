# -*- coding: utf-8 -*-
"""Replay a deterministic benchmark run for the tech-intel pipeline.

This harness is intentionally offline: it uses packaged fixtures and rubric
scoring so prompt/model changes can be checked without AWS credentials or API
keys. It produces a small regression report that answers:

- Did the pipeline still produce a Top 3?
- Did every Top 3 candidate carry enough evidence to be reviewable?
- Did the evidence ledger and human review packet stay well-formed?
- Did governance flags block or downgrade risky candidates?

Example:
  python tools/evaluation_harness.py --out tools/out/benchmark
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAMBDA_SRC = ROOT / "cdk" / "lambda_src"
sys.path.insert(0, str(LAMBDA_SRC))

from pipeline_lib import (  # noqa: E402
    EVAL_WEIGHTS,
    VALIDATE_WEIGHTS,
    build_audit_packet,
    build_decision_layer,
    build_evidence_ledger,
    build_feedback_stats,
    build_review_packet,
    evaluate_article,
    final_rows,
    l0_filter,
    load_case_studies,
    load_packaged_json,
    relevance,
    validate_article,
)


def run_offline_benchmark(run_id):
    raw = load_packaged_json("fixtures.json")
    kept, dropped = l0_filter(raw)
    s1 = {
        "step": "s1_scan",
        "source_mode": "fixtures",
        "fetch_log": [{"source": "packaged fixtures", "kept": len(kept)}],
        "input_count": len(raw),
        "kept_count": len(kept),
        "dropped": dropped,
        "articles": kept,
    }

    ranked = []
    for article in kept:
        item = dict(article)
        item["l1_score"] = relevance(article)
        ranked.append(item)
    ranked.sort(key=lambda item: -item["l1_score"])
    s2 = {
        "step": "s2_compare",
        "input_count": len(ranked),
        "kept_count": min(6, len(ranked)),
        "cut": [{"id": item["id"], "title": item["title"], "l1_score": item["l1_score"]} for item in ranked[6:]],
        "articles": ranked[:6],
    }

    cases = load_case_studies()
    evaluated = [evaluate_article(article, cases) for article in s2["articles"]]
    evaluated.sort(key=lambda item: -item["l2_score"])
    s3 = {
        "step": "s3_evaluate",
        "mode": "offline-rubric-benchmark",
        "quote_decision": "benchmark_offline",
        "evaluator_model": "rubric",
        "rubric_weights": EVAL_WEIGHTS,
        "case_studies_loaded": len(cases),
        "case_studies_ids": [case.get("id", "") for case in cases],
        "input_count": len(evaluated),
        "articles": evaluated,
    }

    rescored = [validate_article(article) for article in evaluated]
    rescored.sort(key=lambda item: -item["v_score"])
    s4 = {
        "step": "s4_validate",
        "mode": "offline-rubric-benchmark",
        "quote_decision": "benchmark_offline",
        "validator_model": "rubric-independent-weights",
        "validator_weights": VALIDATE_WEIGHTS,
        "rescored": rescored,
        "hard_rule_flags": [item for item in rescored if item["flags"]],
    }

    rows = final_rows(s3, s4)
    evidence = build_evidence_ledger(run_id, s1, s2, s3, s4, rows)
    review = build_review_packet(run_id, rows, f"runs/{run_id}/evidence-ledger.json", f"runs/{run_id}/report.html")
    agreement = {
        "n_candidates": len(evaluated),
        "evaluator_top3": [item["id"] for item in evaluated[:3]],
        "validator_top3": [item["id"] for item in rescored[:3]],
        "top3_overlap": len({item["id"] for item in evaluated[:3]} & {item["id"] for item in rescored[:3]}),
        "evaluator_model": "rubric",
        "validator_model": "rubric-independent-weights",
    }
    rq2 = {
        "quote": {"decision": "benchmark_offline", "quoted_usd": None, "actual_llm_usd": 0},
        "tokens": {"input": 0, "output": 0},
    }
    feedback = build_feedback_stats([])
    decision = build_decision_layer(run_id, rows, evidence, agreement=agreement, feedback_stats=feedback)
    keys = {
        "summary_key": f"runs/{run_id}/s5_report.json",
        "report_key": f"runs/{run_id}/report.html",
        "evidence_ledger_key": f"runs/{run_id}/evidence-ledger.json",
        "review_packet_key": f"runs/{run_id}/review-packet.json",
        "decision_layer_key": f"runs/{run_id}/decision-layer.json",
        "feedback_stats_key": f"runs/{run_id}/feedback-stats.json",
        "audit_packet_key": f"runs/{run_id}/audit-packet.json",
        "cost_key": f"runs/{run_id}/cost-estimate.yaml",
    }
    audit = build_audit_packet(run_id, keys, {"decision": "benchmark_offline"}, rq2, agreement, evidence, review, decision, feedback)
    return s1, s2, s3, s4, rows, evidence, review, decision, feedback, audit


def quality_checks(rows, evidence, review, decision, feedback, audit):
    top3 = rows[:3]
    candidate_by_id = {item["id"]: item for item in evidence["candidates"]}
    checks = []

    checks.append({
        "name": "top3_count",
        "passed": len(top3) == 3,
        "detail": f"top3={len(top3)}",
    })
    checks.append({
        "name": "all_candidates_completed_full_flow",
        "passed": len(evidence["candidates"]) == len(rows) and len(rows) >= 3,
        "detail": f"ledger_candidates={len(evidence['candidates'])}, final_rows={len(rows)}",
    })
    checks.append({
        "name": "top3_has_source_urls",
        "passed": all(candidate_by_id[item["id"]].get("source_url") for item in top3),
        "detail": ", ".join(item["id"] for item in top3),
    })
    checks.append({
        "name": "top3_evidence_reviewable",
        "passed": all(candidate_by_id[item["id"]]["evidence_confidence"] in {"medium", "high"} for item in top3),
        "detail": ", ".join(f"{item['id']}={candidate_by_id[item['id']]['evidence_confidence']}" for item in top3),
    })
    checks.append({
        "name": "review_packet_requires_human_action",
        "passed": review.get("status") == "awaiting_human_review"
        and {"approve", "reject", "override", "comment"}.issubset(review.get("required_reviewer_actions", {})),
        "detail": review.get("status", ""),
    })
    checks.append({
        "name": "no_blocked_bedrock_candidate_survived",
        "passed": all("bedrock" not in [tag.lower() for tag in item.get("tags", [])] for item in evidence["candidates"]),
        "detail": "Bedrock-tagged candidates should be dropped by L0 in this company-account variant.",
    })
    checks.append({
        "name": "decision_layer_created",
        "passed": len(decision.get("top3", [])) == 3 and all("decision_score" in item for item in decision.get("top3", [])),
        "detail": ", ".join(f"{item['id']}={item['recommended_action']}" for item in decision.get("top3", [])),
    })
    checks.append({
        "name": "feedback_stats_honest_about_sample_size",
        "passed": feedback.get("sample_status") == "insufficient_for_ml_training",
        "detail": feedback.get("sample_status", ""),
    })
    checks.append({
        "name": "audit_packet_created",
        "passed": bool(audit.get("checks")) and any(check.get("name") == "decision_layer_created" for check in audit.get("checks", [])),
        "detail": audit.get("status", ""),
    })
    return checks


def write_report(out_dir, run_id, rows, evidence, review, decision, feedback, audit, checks):
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "quality_gate": "pass" if all(check["passed"] for check in checks) else "fail",
        "checks": checks,
        "top3": [
            {
                "id": item["id"],
                "title": item["title"],
                "average_score": item["average_score"],
            }
            for item in rows[:3]
        ],
        "evidence_ledger": evidence,
        "review_packet": review,
        "decision_layer": decision,
        "feedback_stats": feedback,
        "audit_packet": audit,
    }
    (out_dir / "benchmark-report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# Tech Intel Evaluation Harness - {run_id}",
        "",
        f"Quality gate: **{payload['quality_gate'].upper()}**",
        "",
        "## Checks",
    ]
    for check in checks:
        mark = "PASS" if check["passed"] else "FAIL"
        lines.append(f"- {mark} `{check['name']}`: {check['detail']}")
    lines += ["", "## Top 3"]
    for idx, item in enumerate(rows[:3], 1):
        lines.append(f"{idx}. `{item['id']}` {item['title']} - average {item['average_score']}")
    lines += ["", "## Decision Layer"]
    for idx, item in enumerate(decision.get("top3", []), 1):
        lines.append(f"{idx}. `{item['id']}` decision_score={item['decision_score']} action={item['recommended_action']}")
    lines += [
        "",
        "## Artifacts",
        "- `benchmark-report.json` contains the evidence ledger, human review packet, decision layer, feedback stats, and audit packet.",
    ]
    (out_dir / "benchmark-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default="offline-benchmark")
    parser.add_argument("--out", default=str(ROOT / "tools" / "out" / "benchmark"))
    args = parser.parse_args()

    _, _, _, _, rows, evidence, review, decision, feedback, audit = run_offline_benchmark(args.run_id)
    checks = quality_checks(rows, evidence, review, decision, feedback, audit)
    payload = write_report(Path(args.out), args.run_id, rows, evidence, review, decision, feedback, audit, checks)
    print(f"quality_gate={payload['quality_gate']}")
    print(f"report={Path(args.out) / 'benchmark-report.md'}")
    if payload["quality_gate"] != "pass":
        sys.exit(1)


if __name__ == "__main__":
    main()
