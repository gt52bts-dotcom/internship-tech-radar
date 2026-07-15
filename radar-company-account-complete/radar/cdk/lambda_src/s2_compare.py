"""Step 2 Lambda: rank surviving concepts against Cathay needs."""
from common import key, read_json, response, run_id_from_event, step_timer, write_json
from pipeline_lib import relevance


def handler(event, context):
    finish_timer = step_timer()
    run_id = run_id_from_event(event)
    s1 = read_json(key(run_id, "s1_scan.json"))
    scored = []
    for article in s1["articles"]:
        item = dict(article)
        item["l1_score"] = relevance(article)
        scored.append(item)
    scored.sort(key=lambda item: -item["l1_score"])
    kept = scored[:6]
    cut = scored[6:]
    output = {
        "step": "s2_compare",
        "input_count": len(scored),
        "kept_count": len(kept),
        "cut": [{"id": item["id"], "title": item["title"], "l1_score": item["l1_score"]} for item in cut],
        "articles": kept,
    }
    output["timing"] = finish_timer()
    out_key = key(run_id, "s2_compare.json")
    write_json(out_key, output)
    return response(run_id, "s2_compare", out_key, {"kept_count": len(kept)})
