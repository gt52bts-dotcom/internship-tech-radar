"""Step 3 Lambda: evaluate every L1 survivor before any final Top-3 decision."""
import json

from common import EVALUATOR_MODEL, assert_role_separation, call_anthropic, key, read_json, response, run_id_from_event, step_timer, write_json
from pipeline_lib import EVAL_WEIGHTS, evaluate_article, load_case_studies


def llm_override(article):
    prompt = f"""You are evaluating an AWS technical radar candidate for Cathay Life.
Return only JSON with integer fields maturity, aws_fit, case_evidence, effort, risk from 1 to 5 and a short rationale.
Higher effort/risk means harder or riskier.

Title: {article['title']}
Summary: {article.get('summary', '')}
Tags: {', '.join(article.get('tags', []))}
Current rubric signals: {json.dumps(article.get('signals', {}), ensure_ascii=False)}
"""
    text = call_anthropic(EVALUATOR_MODEL, prompt)
    if not text:
        return None
    try:
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(text)
        return {name: int(data[name]) for name in ["maturity", "aws_fit", "case_evidence", "effort", "risk"]}, data.get("rationale", "")
    except Exception:
        return None


def handler(event, context):
    assert_role_separation()  # 憲法：建置者 ≠ 驗證者
    finish_timer = step_timer()
    run_id = run_id_from_event(event)
    s2 = read_json(key(run_id, "s2_compare.json"))
    quote = read_json(key(run_id, "quotation.json"))
    llm_approved = quote.get("decision") == "approve"
    cases = load_case_studies()
    evaluated = []
    mode = "api.anthropic.com-with-rubric-fallback" if llm_approved else "rubric-only (quote gate: over budget)"
    for article in s2["articles"]:
        item = evaluate_article(article, cases)
        override = llm_override(item) if llm_approved else None
        if override:
            signals, rationale = override
            item["signals"] = signals
            from pipeline_lib import weighted_score

            item["l2_score"] = weighted_score(signals, EVAL_WEIGHTS)
            item["llm_rationale"] = rationale
        evaluated.append(item)
    evaluated.sort(key=lambda item: -item["l2_score"])
    output = {
        "step": "s3_evaluate",
        "mode": mode,
        "quote_decision": quote.get("decision"),
        "quote_total_usd": quote.get("total_usd"),
        "evaluator_model": EVALUATOR_MODEL,
        "rubric_weights": EVAL_WEIGHTS,
        "case_studies_loaded": len(cases),
        "case_studies_ids": [case.get("id", "") for case in cases],
        "input_count": len(evaluated),
        "articles": evaluated,
    }
    output["timing"] = finish_timer()
    out_key = key(run_id, "s3_evaluate.json")
    write_json(out_key, output)
    return response(run_id, "s3_evaluate", out_key, {"evaluated_count": len(evaluated)})
