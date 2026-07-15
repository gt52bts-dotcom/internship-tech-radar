"""Step 5 Lambda: produce the final report and select Top-3 by average score."""
from decimal import Decimal

from common import key, log_pick, presigned_url, read_json, response, run_id_from_event, step_timer, write_html, write_json, write_text
from pipeline_lib import build_report, cost_estimate_yaml, final_rows


def handler(event, context):
    finish_timer = step_timer()
    run_id = run_id_from_event(event)
    s1 = read_json(key(run_id, "s1_scan.json"))
    s2 = read_json(key(run_id, "s2_compare.json"))
    s3 = read_json(key(run_id, "s3_evaluate.json"))
    s4 = read_json(key(run_id, "s4_validate.json"))
    try:
        quote = read_json(key(run_id, "quotation.json"))
    except Exception:
        quote = None

    rows = final_rows(s3, s4)

    # --- RQ2：AI 端處理時間彙整（誠實量測：wall-clock + 推論 + token）---
    step_timings = {name: data.get("timing", {}) for name, data in [("s1", s1), ("s2", s2), ("s3", s3), ("s4", s4)]}
    ai_wall_seconds = round(sum(t.get("step_wall_seconds", 0) for t in step_timings.values()), 2)
    ai_inference_seconds = round(sum(t.get("llm_usage", {}).get("inference_seconds", 0) for t in step_timings.values()), 2)
    total_tokens = {
        "input": sum(t.get("llm_usage", {}).get("input_tokens", 0) for t in step_timings.values()),
        "output": sum(t.get("llm_usage", {}).get("output_tokens", 0) for t in step_timings.values()),
    }
    actual_llm_usd = None
    if quote:
        prices = {li["role"]: li["unit_price_usd_per_mtok"] for li in quote.get("line_items", [])}
        # 用實際 token × 單價回推實際成本（S3=evaluator、S4=validator）
        def _cost(step, role):
            u = step_timings.get(step, {}).get("llm_usage", {})
            p = prices.get(role, {"input": 0, "output": 0})
            return u.get("input_tokens", 0) / 1e6 * p["input"] + u.get("output_tokens", 0) / 1e6 * p["output"]
        actual_llm_usd = round(_cost("s3", "evaluator") + _cost("s4", "validator"), 4)
    rq2 = {
        "ai_pipeline_wall_seconds": ai_wall_seconds,
        "quote": {
            "quoted_usd": quote.get("total_usd") if quote else None,
            "decision": quote.get("decision") if quote else None,
            "actual_llm_usd": actual_llm_usd,
        },
        "ai_llm_inference_seconds": ai_inference_seconds,
        "tokens": total_tokens,
        "step_timings": step_timings,
        "note": (
            "RQ2 efficiency multiplier = human_total_minutes / (ai_pipeline_wall_seconds/60 "
            "+ human_review_minutes + amortized_maintenance_minutes). "
            "human_review_minutes and maintenance are recorded separately via record_pick / ops log; "
            "inference time alone MUST NOT be reported as the AI-side total."
        ),
    }

    # --- 評估者/驗證者一致度（統計誠實：n 與重疊都要揭露）---
    eval_top3 = [a["id"] for a in s3["articles"][:3]]
    val_top3 = [r["id"] for r in s4["rescored"][:3]]
    agreement = {
        "n_candidates": len(s3["articles"]),
        "n_note": f"n={len(s3['articles'])} is a small daily sample; single-run results are not statistically significant.",
        "evaluator_top3": eval_top3,
        "validator_top3": val_top3,
        "top3_overlap": len(set(eval_top3) & set(val_top3)),
        "evaluator_model": s3.get("evaluator_model", ""),
        "validator_model": s4.get("validator_model", ""),
    }

    summary = {
        "step": "s5_report",
        "selection_rule": "Top 3 by average evaluator/validator score after all five steps",
        "rq2_timing": rq2,
        "agreement": agreement,
        "top3": [
            {
                "id": item["id"],
                "title": item["title"],
                "l2_score": item["l2_score"],
                "validator_score": item["validator_score"],
                "average_score": item["average_score"],
                "url": item.get("url", ""),
            }
            for item in rows[:3]
        ],
        "all_scores": [
            {
                "id": item["id"],
                "title": item["title"],
                "l2_score": item["l2_score"],
                "validator_score": item["validator_score"],
                "average_score": item["average_score"],
                "flags": item["flags"],
            }
            for item in rows
        ],
    }
    summary_key = key(run_id, "s5_report.json")
    report_key = key(run_id, "report.html")
    cost_key = key(run_id, "cost-estimate.yaml")
    latest_key = "reports/latest.html"
    latest_cost_key = "reports/cost-estimate.yaml"
    html = build_report(run_id, s1, s2, s3, s4, research={"agreement": agreement, "rq2_timing": rq2})
    cost_yaml = cost_estimate_yaml()
    write_json(summary_key, summary)
    write_html(report_key, html)
    write_html(latest_key, html)
    write_text(cost_key, cost_yaml, "application/x-yaml; charset=utf-8")
    write_text(latest_cost_key, cost_yaml, "application/x-yaml; charset=utf-8")

    # 把 AI Top3 寫進 DynamoDB pick log（RQ1 盲測：AI 的每日選擇留痕）
    log_pick(run_id, "ai", {
        "judgment_correct": "pending",   # RQ3 閘門：事後由人工判定 correct / incorrect / high_risk_miss
        "ai_wall_seconds": Decimal(str(ai_wall_seconds)),
        "ai_inference_seconds": Decimal(str(ai_inference_seconds)),
        "n_candidates": agreement["n_candidates"],
        "top3_overlap": agreement["top3_overlap"],
        "top3": [
            {
                "id": item["id"],
                "title": item["title"],
                "average_score": Decimal(str(item["average_score"])),
            }
            for item in rows[:3]
        ],
        "candidate_count": len(rows),
        "evaluator_model": s3.get("evaluator_model", ""),
        "validator_model": s4.get("validator_model", ""),
        "report_key": report_key,
    })

    report_url = presigned_url(report_key)
    return response(
        run_id,
        "s5_report",
        report_key,
        {"summary_key": summary_key, "cost_key": cost_key, "latest_key": latest_key, "latest_cost_key": latest_cost_key, "report_url": report_url},
    )
