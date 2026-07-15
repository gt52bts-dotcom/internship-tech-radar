"""Pure-Python pipeline logic shared by the Lambda handlers.

The AWS version intentionally keeps GCP/Azure comparison out of the entry path.
Cross-cloud equivalents are attached only to the final report rows.
"""
import hashlib
import html
import json
import re
from datetime import date
from pathlib import Path

NEEDS_KEYWORDS = {
    "agent": 2.5,
    "stepfunctions": 2.5,
    "step functions": 2.5,
    "lambda": 2.0,
    "serverless": 2.0,
    "orchestration": 2.0,
    "evaluation": 2.0,
    "validation": 2.0,
    "dynamodb": 2.0,
    "s3": 1.5,
    "cloudformation": 1.5,
    "cdk": 1.5,
    "ec2": 1.0,
    "graviton": 1.0,
    "rag": 1.5,
    "embedding": 1.5,
    "vector": 1.5,
    "eventbridge": 1.5,
    "llm": 1.0,
    "nova": 0.5,
    "knowledge-base": 1.0,
    "hitl": 1.5,
    "llm-judge": 2.0,
    "scheduler": 0.5,
    "cost": 0.5,
    "guardrails": 1.5,
    "compliance": 1.5,
}

# 公司政策：Bedrock 被 SCP 封鎖，凡以 Bedrock 為核心的候選一律在 L0 淘汰
BLOCKED_KEYWORDS = {"bedrock"}

CROSS_CLOUD_MAP = {
    "s3": {"aws": "Amazon S3 / S3 Tables / S3 Metadata", "gcp": "Cloud Storage / BigLake", "azure": "Blob Storage / OneLake"},
    "lambda": {"aws": "AWS Lambda (SnapStart)", "gcp": "Cloud Run functions", "azure": "Azure Functions"},
    "serverless": {"aws": "AWS Lambda / Step Functions", "gcp": "Cloud Run / Workflows", "azure": "Functions / Logic Apps"},
    "dynamodb": {"aws": "Amazon DynamoDB", "gcp": "Firestore / Bigtable", "azure": "Cosmos DB"},
    "cloudformation": {"aws": "AWS CloudFormation / CDK", "gcp": "Infrastructure Manager", "azure": "ARM / Bicep"},
    "cdk": {"aws": "AWS CDK", "gcp": "Terraform CDKTF", "azure": "Bicep"},
    "ec2": {"aws": "Amazon EC2 Graviton", "gcp": "Compute Engine (Axion)", "azure": "VMs (Cobalt)"},
    "agent": {"aws": "Amazon Bedrock Agents / AgentCore", "gcp": "Vertex AI Agent Builder", "azure": "Azure AI Foundry Agents"},
    "evaluation": {"aws": "Amazon Bedrock Evaluations", "gcp": "Vertex AI Gen AI Evaluation", "azure": "Azure AI Foundry Evaluation"},
    "validation": {"aws": "Amazon Bedrock Guardrails", "gcp": "Vertex AI Model Armor", "azure": "Azure AI Content Safety"},
    "guardrails": {"aws": "Amazon Bedrock Guardrails", "gcp": "Vertex AI Model Armor", "azure": "Azure AI Content Safety"},
    "rag": {"aws": "Amazon Bedrock Knowledge Bases", "gcp": "Vertex AI Search", "azure": "Azure AI Search"},
    "knowledge-base": {"aws": "Amazon Bedrock Knowledge Bases", "gcp": "Vertex AI Search", "azure": "Azure AI Search"},
    "vector": {"aws": "Amazon S3 Vectors / OpenSearch", "gcp": "Vertex AI Vector Search", "azure": "Azure AI Search vectors"},
    "eventbridge": {"aws": "Amazon EventBridge Scheduler", "gcp": "Cloud Scheduler", "azure": "Azure Logic Apps / Scheduler"},
    "stepfunctions": {"aws": "AWS Step Functions", "gcp": "Workflows", "azure": "Durable Functions"},
}

EVAL_WEIGHTS = {"maturity": 0.35, "aws_fit": 0.25, "case_evidence": 0.15, "effort": 0.15, "risk": 0.10}
VALIDATE_WEIGHTS = {"maturity": 0.20, "aws_fit": 0.20, "case_evidence": 0.20, "effort": 0.20, "risk": 0.20}
PACKAGE_DIR = Path(__file__).parent
DATA_DIR = PACKAGE_DIR / "data"

COST_ESTIMATE = {
    "project": "cathay-techintel-v3",
    "region": "ap-southeast-1",
    "budget_usd": 100,
    "estimated_monthly_usd_range": [5, 15],
    "bedrock_enabled": False,
    "anthropic_via": "api.anthropic.com (key in Secrets Manager)",
    "decision": "within_budget",
    "services": [
        {"name": "S3", "purpose": "pipeline JSON + HTML reports; lifecycle expires runs/ after 90 days", "estimate_usd": 1},
        {"name": "Lambda", "purpose": "run S1-S5", "estimate_usd": 1},
        {"name": "Step Functions", "purpose": "orchestrate five-step workflow", "estimate_usd": 1},
        {"name": "DynamoDB", "purpose": "AI/human pick log with TTL (RQ1 blind-test data)", "estimate_usd": 1},
        {"name": "Secrets Manager", "purpose": "store Anthropic API key", "estimate_usd": 0.4},
        {"name": "EventBridge Scheduler", "purpose": "daily 08:00 Taipei trigger (default disabled)", "estimate_usd": 0},
        {"name": "CloudWatch Logs", "purpose": "execution logs, 14-day retention", "estimate_usd_range": [1, 3]},
        {"name": "Anthropic API", "purpose": "evaluator (Sonnet 4.5) + validator (Haiku 4.5) calls", "estimate_usd": "usage-based; ~USD 0.09 per approved run"},
    ],
    "excluded_services": [
        "Amazon Bedrock (blocked by SCP)",
        "CloudFront (global service; region-restricted account)",
        "Customer-managed KMS (replaced by SSE-S3 / AWS-managed)",
        "OpenSearch", "RDS", "EC2",
    ],
}


def load_packaged_json(name):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def load_case_studies():
    case_dir = DATA_DIR / "case_studies"
    cases = []
    for file in sorted(case_dir.glob("*.json")):
        with open(file, encoding="utf-8") as f:
            cases.append(json.load(f))
    return cases


def strip_html(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", value or "")).strip()


def source_mode_and_articles():
    """Fetch RSS when possible; fall back to packaged fixtures for deterministic deploy tests."""
    sources = load_packaged_json("sources.json")
    try:
        import feedparser

        articles = []
        fetch_log = []
        for src in sources.get("sources", []):
            if not src.get("enabled"):
                continue
            feed = feedparser.parse(src["url"])
            kept = 0
            for entry in feed.entries[: src.get("max_items", 10)]:
                title = getattr(entry, "title", "").strip()
                url = getattr(entry, "link", "")
                summary = strip_html(getattr(entry, "summary", ""))[:500]
                if not title or not url:
                    continue
                text = f"{title} {summary}".lower()
                tags = [tag for tag in list(NEEDS_KEYWORDS) + sorted(BLOCKED_KEYWORDS) if tag.replace("-", " ") in text or tag in text]
                if not tags:
                    continue
                articles.append(
                    {
                        "id": "R-" + hashlib.md5(url.encode("utf-8")).hexdigest()[:8].upper(),
                        "title": title,
                        "source": src["name"],
                        "date": date.today().isoformat(),
                        "url": url,
                        "summary": summary or title,
                        "cloud": "aws",
                        "tags": tags,
                        "status": "unknown",
                        "signals": {"maturity": 3, "aws_fit": 5, "effort": 3, "risk": 3},
                    }
                )
                kept += 1
            fetch_log.append({"source": src["name"], "kept": kept})
        if articles:
            return "rss", articles, fetch_log
    except Exception as exc:
        fetch_log = [{"source": "rss", "error": str(exc)}]

    return "fixtures", load_packaged_json("fixtures.json"), fetch_log


def l0_filter(articles):
    kept, dropped, seen = [], [], set()
    for article in articles:
        reason = None
        digest = hashlib.md5(article["title"].strip().encode("utf-8")).hexdigest()[:10]
        if any(tag in BLOCKED_KEYWORDS for tag in article.get("tags", [])):
            reason = "Bedrock is blocked by Cathay SCP policy; excluded from radar"
        elif not any(tag in NEEDS_KEYWORDS for tag in article.get("tags", [])):
            reason = "No match with Cathay AI/cloud radar needs"
        elif article.get("status", "").lower() in {"preview", "beta"}:
            reason = f"Skipped because status is {article.get('status')}"
        elif digest in seen:
            reason = "Duplicate title"
        if reason:
            dropped.append({"id": article["id"], "title": article["title"], "reason": reason})
        else:
            seen.add(digest)
            kept.append(article)
    return kept, dropped


def relevance(article):
    return round(sum(NEEDS_KEYWORDS.get(tag, 0) for tag in article.get("tags", [])), 2)


def cross_cloud(article):
    rows = []
    for tag in article.get("tags", []):
        if tag in CROSS_CLOUD_MAP:
            rows.append({"capability": tag, **CROSS_CLOUD_MAP[tag]})
    return rows


def match_cases(article, cases):
    art_tags = set(article.get("tags", []))
    matched = []
    for case in cases:
        overlap = art_tags & set(case.get("matched_technologies", []))
        if overlap:
            matched.append(
                {
                    "id": case.get("id", ""),
                    "customer": case.get("customer", ""),
                    "overlap_tags": sorted(overlap),
                    "relevance_to_cathay": case.get("relevance_to_cathay", {}).get("score", 3),
                }
            )
    return sorted(matched, key=lambda item: -item["relevance_to_cathay"])


def case_score(matches):
    if not matches:
        return 2
    top = matches[0]["relevance_to_cathay"]
    if len(matches) >= 2 and top >= 5:
        return 5
    if len(matches) >= 2 or top >= 5:
        return 4
    return 3


def weighted_score(signals, weights):
    return round(
        signals["maturity"] * weights["maturity"]
        + signals["aws_fit"] * weights["aws_fit"]
        + signals.get("case_evidence", 2) * weights["case_evidence"]
        + (6 - signals["effort"]) * weights["effort"]
        + (6 - signals["risk"]) * weights["risk"],
        2,
    )


def local_reason(article, matches):
    parts = []
    signals = article["signals"]
    if signals["aws_fit"] >= 4:
        parts.append("AWS fit is high for the current Cathay-oriented radar.")
    if signals["maturity"] >= 4:
        parts.append("Maturity is enough for PoC planning.")
    if matches:
        parts.append(f"Enterprise evidence found: {matches[0]['customer']}.")
    else:
        parts.append("No strong enterprise case evidence yet.")
    if signals["risk"] >= 4:
        parts.append("Risk needs extra governance review.")
    return " ".join(parts)


def evaluate_article(article, cases):
    matches = match_cases(article, cases)
    signals = dict(article.get("signals", {}))
    signals["case_evidence"] = case_score(matches)
    evaluated = dict(article)
    evaluated["matched_cases"] = matches
    evaluated["signals"] = signals
    evaluated["l2_score"] = weighted_score(signals, EVAL_WEIGHTS)
    evaluated["reason"] = local_reason(evaluated, matches)
    return evaluated


def validate_article(article):
    signals = dict(article["signals"])
    v_score = weighted_score(signals, VALIDATE_WEIGHTS)
    flags = []
    if signals["risk"] >= 4:
        flags.append("High risk; require human review before PoC.")
    if signals["maturity"] <= 2:
        flags.append("Low maturity; keep in Assess instead of PoC.")
    return {"id": article["id"], "title": article["title"], "v_score": v_score, "flags": flags}


def final_rows(s3_eval, s4_validate):
    validators = {row["id"]: row for row in s4_validate["rescored"]}
    rows = []
    for article in s3_eval["articles"]:
        validator = validators.get(article["id"], {"v_score": 0, "flags": []})
        avg = round((article["l2_score"] + validator["v_score"]) / 2, 2)
        row = dict(article)
        row["validator_score"] = validator["v_score"]
        row["average_score"] = avg
        row["flags"] = validator["flags"]
        row["cross_cloud"] = cross_cloud(article)
        rows.append(row)
    return sorted(rows, key=lambda item: (-item["average_score"], -item["l2_score"]))


def build_report(run_id, s1, s2, s3, s4, research=None):
    rows = final_rows(s3, s4)
    if research:
        agr = research.get("agreement", {})
        rq2 = research.get("rq2_timing", {})
        research_block = (
            f"<p><b>n = {agr.get('n_candidates', '?')}</b>（單日樣本，單次結果不具統計顯著性；RQ1 結論需累積多日盲測資料）</p>"
            f"<p>評估者（{html.escape(str(agr.get('evaluator_model','')))}）與驗證者（{html.escape(str(agr.get('validator_model','')))}）"
            f"Top3 重疊：<b>{agr.get('top3_overlap','?')}/3</b> — 憲法要求兩者為不同模型，程式碼層已強制。</p>"
            f"<p>AI 端本次耗時：管線 wall-clock <b>{rq2.get('ai_pipeline_wall_seconds','?')} 秒</b>"
            f"（其中 LLM 推論 {rq2.get('ai_llm_inference_seconds','?')} 秒，"
            f"tokens in/out {rq2.get('tokens',{}).get('input','?')}/{rq2.get('tokens',{}).get('output','?')}）。"
            f"RQ2 效率倍數須另計人類審查與系統維護時間，不得僅以推論時間計算。</p>"
            + (
                f"<p>報價閘門：本次報價 <b>${rq2['quote']['quoted_usd']}</b>（{html.escape(str(rq2['quote']['decision']))}）"
                f"，實際 LLM 花費 <b>${rq2['quote']['actual_llm_usd']}</b> — 估 vs 實留痕供閘門校準。</p>"
                if rq2.get("quote", {}).get("quoted_usd") is not None else ""
            )
        )
    else:
        research_block = "<p>本次執行未附研究統計。</p>"
    top3 = rows[:3]
    cards = []
    for idx, article in enumerate(top3, 1):
        case_text = "".join(
            f"<li>{html.escape(m['customer'])} ({m['relevance_to_cathay']}/5)</li>"
            for m in article.get("matched_cases", [])[:3]
        ) or "<li>No direct enterprise case yet</li>"
        cloud_rows = "".join(
            "<tr>"
            f"<td>{html.escape(r['capability'])}</td>"
            f"<td>{html.escape(r['aws'])}</td>"
            f"<td>{html.escape(r['gcp'])}</td>"
            f"<td>{html.escape(r['azure'])}</td>"
            "</tr>"
            for r in article.get("cross_cloud", [])
        )
        cards.append(
            f"""
            <article class="pick">
              <div class="rank">{idx}</div>
              <div>
                <h3>{html.escape(article['title'])}</h3>
                <p class="meta">{html.escape(article['source'])} | {html.escape(article.get('date', ''))} | avg {article['average_score']}</p>
                <p>{html.escape(article.get('summary', ''))}</p>
                <p class="reason">{html.escape(article.get('reason', ''))}</p>
                <h4>Cathay application scenario</h4>
                <p>Use this as a controlled internal PoC candidate for insurance operations, compliance review, knowledge retrieval, or AI governance depending on its tags. Start with a small team, measure decision quality, time saved, and risk controls before wider rollout.</p>
                <h4>Evidence</h4>
                <ul>{case_text}</ul>
                <h4>GCP / Azure equivalent services</h4>
                <table><tr><th>Capability</th><th>AWS</th><th>GCP</th><th>Azure</th></tr>{cloud_rows}</table>
              </div>
            </article>
            """
        )
    all_rows = "".join(
        f"<tr><td>{html.escape(r['id'])}</td><td>{html.escape(r['title'])}</td><td>{r['l2_score']}</td><td>{r['validator_score']}</td><td>{r['average_score']}</td></tr>"
        for r in rows
    )
    cost_rows = "".join(
        "<tr>"
        f"<td>{html.escape(item['name'])}</td>"
        f"<td>{html.escape(item['purpose'])}</td>"
        f"<td>{html.escape(str(item.get('estimate_usd', item.get('estimate_usd_range', 'variable'))))}</td>"
        "</tr>"
        for item in COST_ESTIMATE["services"]
    )
    excluded = "".join(f"<li>{html.escape(name)}</li>" for name in COST_ESTIMATE["excluded_services"])
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <title>Cathay Tech Intel Report {html.escape(run_id)}</title>
  <style>
    body {{ font-family: "Microsoft JhengHei", Arial, sans-serif; margin: 0; background: #f5f7f8; color: #152328; line-height: 1.65; }}
    header {{ background: #0b3f4a; color: white; padding: 28px 36px; }}
    main {{ max-width: 980px; margin: 0 auto; padding: 28px 20px 56px; }}
    .pick {{ display: grid; grid-template-columns: 42px 1fr; gap: 16px; background: white; border: 1px solid #d9e2e4; border-radius: 6px; padding: 18px; margin-bottom: 18px; }}
    .rank {{ color: #0b6477; font-size: 28px; font-weight: 700; }}
    .meta {{ color: #60747b; font-size: 13px; }}
    .reason {{ background: #edf5f6; padding: 8px 10px; border-radius: 4px; }}
    h2 {{ color: #0b6477; margin-top: 30px; }}
    h3 {{ margin: 0; }}
    h4 {{ margin: 14px 0 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 8px; font-size: 13px; }}
    th, td {{ border: 1px solid #d9e2e4; padding: 6px 8px; text-align: left; }}
    th {{ background: #edf5f6; }}
  </style>
</head>
<body>
<header>
  <div>Daily AWS Technical Radar</div>
  <h1>Cathay Tech Intel v3 Report</h1>
  <p>Run ID: {html.escape(run_id)} | Source: {html.escape(s1['source_mode'])} | Final winners selected after all five steps by average score.</p>
</header>
<main>
  <h2>Final Top 3</h2>
  {''.join(cards)}
  <h2>System Scoring Report</h2>
  <table><tr><th>ID</th><th>Concept</th><th>Evaluator</th><th>Validator</th><th>Average</th></tr>{all_rows}</table>
  <h2>Budget Quotation</h2>
  <p>This implementation is designed to stay within the USD {COST_ESTIMATE['budget_usd']} company-account landing-validation budget. Estimated monthly AWS cost for light usage is USD {COST_ESTIMATE['estimated_monthly_usd_range'][0]}-{COST_ESTIMATE['estimated_monthly_usd_range'][1]}. Amazon Bedrock and CloudFront are intentionally excluded, and Anthropic API calls are controlled by the per-run quote gate.</p>
  <table><tr><th>Service</th><th>Purpose</th><th>Estimate USD/month</th></tr>{cost_rows}</table>
  <h3>Excluded for Budget Control</h3>
  <ul>{excluded}</ul>
  <h2>Pipeline Funnel</h2>
  <p>Fetched {s1['input_count']} concepts, kept {s1['kept_count']} after L0, ranked {s2['kept_count']} through L1, evaluated {s3['input_count']} through L2, and validated {len(s4['rescored'])} before final selection.</p>
  <h2>Research disclosure（統計誠實揭露）</h2>
  {research_block}
</main>
</body>
</html>"""


def cost_estimate_yaml():
    lines = [
        "project: cathay-techintel-v3",
        "region: ap-southeast-1",
        "budget:",
        "  currency: USD",
        f"  max_total: {COST_ESTIMATE['budget_usd']}",
        "  status: within_budget",
        "cost_policy:",
        "  use_bedrock: false",
        "  use_anthropic_api: optional",
        "  default_ai_mode: rubric_fallback",
        "  avoid_high_fixed_cost_services:",
    ]
    lines += [f"    - {name}" for name in COST_ESTIMATE["excluded_services"]]
    lines += [
        "estimated_monthly_cost:",
    ]
    for item in COST_ESTIMATE["services"]:
        key_name = item["name"].lower().replace(" ", "_")
        lines.append(f"  {key_name}:")
        lines.append(f"    purpose: {item['purpose']}")
        if "estimate_usd" in item:
            lines.append(f"    estimate_usd: {item['estimate_usd']}")
        else:
            lo, hi = item["estimate_usd_range"]
            lines.append(f"    estimate_usd_range: [{lo}, {hi}]")
    lo, hi = COST_ESTIMATE["estimated_monthly_usd_range"]
    lines += [
        f"estimated_total_monthly_usd_range: [{lo}, {hi}]",
        "implementation_decision: proceed",
        "notes:",
        '  - "Bedrock is intentionally excluded for this phase."',
        '  - "Anthropic API is controlled by the quote gate; over-budget runs fall back to zero-token rubric mode."',
        '  - "Run cdk destroy --all after landing validation if the environment is no longer needed."',
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# 報價閘門（Quote Gate）：執行 LLM 前先報價，報價合理才下去做
# 定價來源：Anthropic 官方（2026-07 查核）
# ---------------------------------------------------------------------------
ANTHROPIC_PRICING_USD_PER_MTOK = {
    "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5": {"input": 1.0, "output": 5.0},
}
# 每候選的 token 估算（依 s3/s4 prompt 實測長度抓上緣，寧可高估不可低估）
EST_TOKENS_PER_CANDIDATE = {
    "evaluator": {"input": 1500, "output": 400},
    "validator": {"input": 1200, "output": 300},
}
# 每次執行的固定 AWS 成本（Lambda/SFN/S3/DDB 攤提，抓保守上緣）
EST_AWS_FIXED_USD_PER_RUN = 0.01


def build_quotation(candidate_count, evaluator_model, validator_model, max_run_usd):
    """執行前報價：回傳報價單 dict，含 approve / fallback_rubric 決策。"""
    def model_cost(model, role):
        price = ANTHROPIC_PRICING_USD_PER_MTOK.get(model, {"input": 5.0, "output": 25.0})
        est = EST_TOKENS_PER_CANDIDATE[role]
        cost = candidate_count * (
            est["input"] / 1_000_000 * price["input"]
            + est["output"] / 1_000_000 * price["output"]
        )
        return {
            "model": model,
            "role": role,
            "candidates": candidate_count,
            "est_input_tokens": candidate_count * est["input"],
            "est_output_tokens": candidate_count * est["output"],
            "unit_price_usd_per_mtok": price,
            "est_cost_usd": round(cost, 4),
        }

    lines = [
        model_cost(evaluator_model, "evaluator"),
        model_cost(validator_model, "validator"),
    ]
    llm_total = round(sum(line["est_cost_usd"] for line in lines), 4)
    total = round(llm_total + EST_AWS_FIXED_USD_PER_RUN, 4)
    decision = "approve" if total <= max_run_usd else "fallback_rubric"
    return {
        "quotation_version": "1.0",
        "pricing_source": "Anthropic official pricing, verified 2026-07",
        "line_items": lines,
        "aws_fixed_usd": EST_AWS_FIXED_USD_PER_RUN,
        "llm_total_usd": llm_total,
        "total_usd": total,
        "max_run_usd": max_run_usd,
        "decision": decision,
        "decision_rule": f"total_usd <= max_run_usd ({max_run_usd}) → approve; otherwise fallback to zero-token rubric mode",
    }


def build_quotation_html(run_id, quote):
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(li['role'])}</td>"
        f"<td>{html.escape(li['model'])}</td>"
        f"<td>{li['candidates']}</td>"
        f"<td>{li['est_input_tokens']:,} / {li['est_output_tokens']:,}</td>"
        f"<td>${li['unit_price_usd_per_mtok']['input']}/{li['unit_price_usd_per_mtok']['output']} per MTok</td>"
        f"<td>${li['est_cost_usd']}</td>"
        "</tr>"
        for li in quote["line_items"]
    )
    color = "#0a7d32" if quote["decision"] == "approve" else "#b3261e"
    verdict = "核准執行（APPROVE）" if quote["decision"] == "approve" else "超出上限 → 改走零 token rubric 模式"
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>執行前報價單 {html.escape(run_id)}</title>
<style>body{{font-family:system-ui,'Noto Sans TC',sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;color:#1b1b1f}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ccc;padding:.5rem .6rem;text-align:left}}
th{{background:#f2f2f6}}.verdict{{font-size:1.2rem;font-weight:700;color:{color}}}</style></head><body>
<h1>技術雷達 Pipeline 執行前報價單</h1>
<p>Run ID：{html.escape(run_id)}｜報價依據：{html.escape(quote['pricing_source'])}</p>
<table><tr><th>角色</th><th>模型</th><th>候選數</th><th>估 tokens（in/out）</th><th>單價</th><th>估算成本</th></tr>{rows}</table>
<p>LLM 小計：<b>${quote['llm_total_usd']}</b>｜AWS 固定攤提：${quote['aws_fixed_usd']}｜
<b>本次總報價：${quote['total_usd']}</b>（上限 ${quote['max_run_usd']}）</p>
<p class="verdict">{verdict}</p>
<p>規則：{html.escape(quote['decision_rule'])}</p>
</body></html>"""
