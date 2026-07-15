"""Quote Gate Lambda：在花任何 LLM token 之前先報價。

決策規則：估算總成本 <= MAX_RUN_USD → approve（S3/S4 可呼叫 LLM）；
否則 fallback_rubric（S3/S4 改走零 token 規則評分，pipeline 照樣完成）。
報價單同時存 JSON（機器讀）與 HTML（給主管看）。
"""
import os

from common import EVALUATOR_MODEL, VALIDATOR_MODEL, key, read_json, response, run_id_from_event, step_timer, write_html, write_json
from pipeline_lib import build_quotation, build_quotation_html

MAX_RUN_USD = float(os.environ.get("MAX_RUN_USD", "0.50"))


def handler(event, context):
    finish_timer = step_timer()
    run_id = run_id_from_event(event)
    s2 = read_json(key(run_id, "s2_compare.json"))
    quote = build_quotation(
        candidate_count=s2["kept_count"],
        evaluator_model=EVALUATOR_MODEL,
        validator_model=VALIDATOR_MODEL,
        max_run_usd=MAX_RUN_USD,
    )
    quote["step"] = "s2b_quote"
    quote["timing"] = finish_timer()
    out_key = key(run_id, "quotation.json")
    write_json(out_key, quote)
    write_html(key(run_id, "quotation.html"), build_quotation_html(run_id, quote))
    return response(run_id, "s2b_quote", out_key, {
        "decision": quote["decision"],
        "total_usd": quote["total_usd"],
        "max_run_usd": MAX_RUN_USD,
    })
