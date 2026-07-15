"""Step 1 Lambda: gather AWS concepts and run deterministic L0 filtering."""
from common import key, response, run_id_from_event, step_timer, write_json
from pipeline_lib import l0_filter, source_mode_and_articles


def handler(event, context):
    finish_timer = step_timer()
    run_id = run_id_from_event(event)
    source_mode, raw, fetch_log = source_mode_and_articles()
    kept, dropped = l0_filter(raw)
    output = {
        "step": "s1_scan",
        "source_mode": source_mode,
        "fetch_log": fetch_log,
        "input_count": len(raw),
        "kept_count": len(kept),
        "dropped": dropped,
        "articles": kept,
    }
    output["timing"] = finish_timer()
    out_key = key(run_id, "s1_scan.json")
    write_json(out_key, output)
    return response(run_id, "s1_scan", out_key, {"kept_count": len(kept)})
