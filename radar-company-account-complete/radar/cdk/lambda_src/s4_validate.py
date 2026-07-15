"""Step 4 Lambda: independently rescore all evaluated concepts."""
import json

from common import VALIDATOR_MODEL, assert_role_separation, call_anthropic, key, read_json, response, run_id_from_event, step_timer, write_json
from pipeline_lib import VALIDATE_WEIGHTS, validate_article, weighted_score


def llm_validate(article):
    prompt = f"""You are an independent validator for a Cathay Life AWS radar candidate.
Do not rubber-stamp the evaluator. Return only JSON with maturity, aws_fit, case_evidence, effort, risk from 1 to 5.

Title: {article['title']}
Summary: {article.get('summary', '')}
Evaluator signals: {json.dumps(article.get('signals', {}), ensure_ascii=False)}
Evaluator rationale: {article.get('llm_rationale', article.get('reason', ''))}
"""
    text = call_anthropic(VALIDATOR_MODEL, prompt)
    if not text:
        return None
    try:
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(text)
        signals = {name: int(data[name]) for name in ["maturity", "aws_fit", "case_evidence", "effort", "risk"]}
        flags = []
        if signals["risk"] >= 4:
            flags.append("High risk; require human review before PoC.")
        if signals["maturity"] <= 2:
            flags.append("Low maturity; keep in Assess instead of PoC.")
        return {"id": article["id"], "title": article["title"], "v_score": weighted_score(signals, VALIDATE_WEIGHTS), "flags": flags}
    except Exception:
        return None


def handler(event, context):
    assert_role_separation()  # 憲法：建置者 ≠ 驗證者
    finish_timer = step_timer()
    run_id = run_id_from_event(event)
    s3 = read_json(key(run_id, "s3_evaluate.json"))
    quote = read_json(key(run_id, "quotation.json"))
    llm_approved = quote.get("decision") == "approve"
    rescored = []
    for article in s3["articles"]:
        rescored.append((llm_validate(article) if llm_approved else None) or validate_article(article))
    rescored.sort(key=lambda item: -item["v_score"])
    output = {
        "step": "s4_validate",
        "mode": "api.anthropic.com-with-rubric-fallback" if llm_approved else "rubric-only (quote gate: over budget)",
        "quote_decision": quote.get("decision"),
        "validator_model": VALIDATOR_MODEL,
        "validator_weights": VALIDATE_WEIGHTS,
        "rescored": rescored,
        "hard_rule_flags": [item for item in rescored if item["flags"]],
    }
    output["timing"] = finish_timer()
    out_key = key(run_id, "s4_validate.json")
    write_json(out_key, output)
    return response(run_id, "s4_validate", out_key, {"validated_count": len(rescored)})
