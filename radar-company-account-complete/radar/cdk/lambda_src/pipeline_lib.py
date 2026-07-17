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


def governance_flags(article, validator_flags=None):
    """Attach decision-governance flags that can be audited later."""
    flags = list(validator_flags or [])
    signals = article.get("signals", {})
    if not article.get("url"):
        flags.append("Missing source URL; evidence trace is incomplete.")
    if not article.get("matched_cases"):
        flags.append("Weak enterprise case evidence; require reviewer confirmation.")
    if signals.get("risk", 0) >= 4:
        flags.append("High risk score; human approval required before PoC.")
    if signals.get("maturity", 5) <= 2:
        flags.append("Low maturity; keep in Assess/Hold until stronger evidence appears.")
    return sorted(set(flags))


def evidence_confidence(article):
    score = 0
    if article.get("url"):
        score += 1
    if article.get("summary"):
        score += 1
    if article.get("matched_cases"):
        score += 1
    if article.get("reason") or article.get("llm_rationale"):
        score += 1
    if article.get("signals"):
        score += 1
    if score >= 5:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def radar_ring(article):
    """Map final scores to a familiar tech-radar decision language."""
    flags = governance_flags(article, article.get("flags", []))
    avg = article.get("average_score", 0)
    if any("High risk" in flag or "Low maturity" in flag for flag in flags):
        return "Assess"
    if avg >= 4.3:
        return "Adopt"
    if avg >= 3.8:
        return "Trial"
    if avg >= 3.0:
        return "Assess"
    return "Hold"


def build_evidence_ledger(run_id, s1, s2, s3, s4, rows):
    """Build a machine-readable evidence chain for every surviving candidate."""
    l1_by_id = {item["id"]: item for item in s2.get("articles", [])}
    validator_by_id = {item["id"]: item for item in s4.get("rescored", [])}
    candidates = []
    for article in rows:
        validator = validator_by_id.get(article["id"], {})
        flags = governance_flags(article, validator.get("flags", []))
        candidates.append(
            {
                "id": article["id"],
                "title": article["title"],
                "source": article.get("source", ""),
                "source_url": article.get("url", ""),
                "source_date": article.get("date", ""),
                "summary": article.get("summary", ""),
                "tags": article.get("tags", []),
                "status": article.get("status", "unknown"),
                "evidence_confidence": evidence_confidence(article),
                "radar_ring": radar_ring({**article, "flags": flags}),
                "scores": {
                    "l1_relevance": l1_by_id.get(article["id"], {}).get("l1_score"),
                    "l2_evaluator": article.get("l2_score"),
                    "validator": validator.get("v_score"),
                    "average": article.get("average_score"),
                },
                "rationale": {
                    "rubric_reason": article.get("reason", ""),
                    "llm_rationale": article.get("llm_rationale", ""),
                    "validator_flags": validator.get("flags", []),
                    "governance_flags": flags,
                },
                "evidence": {
                    "matched_enterprise_cases": article.get("matched_cases", []),
                    "cross_cloud_equivalents": article.get("cross_cloud", []),
                    "signals": article.get("signals", {}),
                },
                "trace": {
                    "s1_scan": {"source_mode": s1.get("source_mode"), "kept_count": s1.get("kept_count")},
                    "s2_compare": {"kept_count": s2.get("kept_count"), "l1_ranked": article["id"] in l1_by_id},
                    "s3_evaluate": {"mode": s3.get("mode"), "model": s3.get("evaluator_model")},
                    "s4_validate": {"mode": s4.get("mode"), "model": s4.get("validator_model")},
                    "s5_report": {"selection_rule": "Top 3 by average evaluator/validator score after all five steps"},
                },
            }
        )
    return {
        "ledger_version": "1.0",
        "run_id": run_id,
        "purpose": "Auditable evidence ledger for AI-assisted technology radar decisions.",
        "controls": {
            "single_entry_flow": True,
            "top3_after_full_flow": True,
            "human_review_required_for_top3": True,
            "review_actions": ["approve", "reject", "override", "comment"],
        },
        "pipeline_counts": {
            "s1_input": s1.get("input_count"),
            "s1_kept": s1.get("kept_count"),
            "s2_kept": s2.get("kept_count"),
            "s3_evaluated": s3.get("input_count"),
            "s4_validated": len(s4.get("rescored", [])),
        },
        "candidates": candidates,
    }


def build_review_packet(run_id, rows, evidence_ledger_key, report_key):
    top3 = rows[:3]
    return {
        "review_packet_version": "1.0",
        "run_id": run_id,
        "status": "awaiting_human_review",
        "review_goal": "Approve, reject, override, or comment on the AI Top 3 before treating it as an implementation recommendation.",
        "ai_top3": [
            {
                "rank": idx,
                "id": item["id"],
                "title": item["title"],
                "average_score": item["average_score"],
                "radar_ring": radar_ring(item),
                "evidence_confidence": evidence_confidence(item),
                "governance_flags": governance_flags(item, item.get("flags", [])),
            }
            for idx, item in enumerate(top3, 1)
        ],
        "required_reviewer_actions": {
            "approve": "Accept AI Top 3 as the current daily recommendation.",
            "reject": "Reject the AI Top 3 and record why.",
            "override": "Provide a replacement picked_ids list and rationale.",
            "comment": "Keep decision pending but add reviewer feedback.",
        },
        "record_human_pick_payload_example": {
            "run_id": run_id,
            "reviewer": "reviewer-name",
            "decision": "approve",
            "picked_ids": [item["id"] for item in top3],
            "human_minutes": 15,
            "blind": False,
            "note": "Reviewed evidence ledger and accepted current Top 3.",
        },
        "artifacts": {
            "report_key": report_key,
            "evidence_ledger_key": evidence_ledger_key,
        },
    }


def _as_id_list(value):
    if not value:
        return []
    if isinstance(value, list):
        ids = []
        for item in value:
            if isinstance(item, dict):
                ids.append(str(item.get("id", "")))
            else:
                ids.append(str(item))
        return [item for item in ids if item]
    return [str(value)]


def build_feedback_stats(pick_items):
    """Summarize AI/human decision logs without pretending we have enough ML labels."""
    by_run = {}
    for item in pick_items or []:
        run_id = str(item.get("run_id", ""))
        if not run_id:
            continue
        by_run.setdefault(run_id, []).append(item)

    ai_runs = 0
    human_reviews = 0
    approvals = 0
    rejections = 0
    overrides = 0
    comment_only = 0
    blind_reviews = 0
    human_minutes = []
    overlaps = []
    approved_ids = {}
    rejected_ids = {}

    for items in by_run.values():
        ai_items = [item for item in items if item.get("actor") == "ai"]
        human_items = [item for item in items if item.get("actor") == "human"]
        ai_runs += len(ai_items)
        human_reviews += len(human_items)
        for human in human_items:
            decision = str(human.get("decision", "")).lower()
            approvals += 1 if decision == "approve" else 0
            rejections += 1 if decision == "reject" else 0
            overrides += 1 if decision == "override" else 0
            comment_only += 1 if decision == "comment" or human.get("review_status") == "comment_only" else 0
            blind_reviews += 1 if human.get("blind") is True else 0
            if human.get("human_minutes") not in (None, ""):
                try:
                    human_minutes.append(float(human.get("human_minutes", 0)))
                except Exception:
                    pass
            picked_ids = _as_id_list(human.get("picked_ids"))
            target = rejected_ids if decision == "reject" else approved_ids
            for item_id in picked_ids:
                target[item_id] = target.get(item_id, 0) + 1
        if ai_items and human_items:
            ai_top = set(_as_id_list(ai_items[-1].get("top3")))
            for human in human_items:
                human_top = set(_as_id_list(human.get("picked_ids")))
                if ai_top and human_top:
                    overlaps.append(round(len(ai_top & human_top) / min(3, len(ai_top)), 2))

    avg_minutes = round(sum(human_minutes) / len(human_minutes), 2) if human_minutes else None
    avg_overlap = round(sum(overlaps) / len(overlaps), 2) if overlaps else None
    sample_status = "sufficient_for_trend" if human_reviews >= 5 else "insufficient_for_ml_training"
    return {
        "feedback_stats_version": "1.0",
        "sample_status": sample_status,
        "sample_note": (
            "This is descriptive feedback telemetry, not a trained ML model. "
            "Use it for trend evidence now; promote to ML calibration only after enough labeled human reviews accumulate."
        ),
        "counts": {
            "runs_with_logs": len(by_run),
            "ai_pick_logs": ai_runs,
            "human_review_logs": human_reviews,
            "approvals": approvals,
            "rejections": rejections,
            "overrides": overrides,
            "comment_only": comment_only,
            "blind_reviews": blind_reviews,
        },
        "metrics": {
            "approval_rate": round(approvals / human_reviews, 2) if human_reviews else None,
            "override_rate": round(overrides / human_reviews, 2) if human_reviews else None,
            "average_human_review_minutes": avg_minutes,
            "average_ai_human_top3_overlap": avg_overlap,
        },
        "signals": {
            "approved_ids": approved_ids,
            "rejected_ids": rejected_ids,
        },
    }


def build_decision_layer(run_id, rows, evidence_ledger, agreement=None, feedback_stats=None):
    """Explainable algorithmic decision layer above raw average score."""
    agreement = agreement or {}
    feedback_stats = feedback_stats or {}
    candidates = {item["id"]: item for item in evidence_ledger.get("candidates", [])}
    evaluator_top3 = set(agreement.get("evaluator_top3", []))
    validator_top3 = set(agreement.get("validator_top3", []))
    approved_ids = feedback_stats.get("signals", {}).get("approved_ids", {})
    rejected_ids = feedback_stats.get("signals", {}).get("rejected_ids", {})
    decisions = []

    for row in rows:
        evidence = candidates.get(row["id"], {})
        flags = evidence.get("rationale", {}).get("governance_flags", [])
        confidence = evidence.get("evidence_confidence", "low")
        matched_cases = evidence.get("evidence", {}).get("matched_enterprise_cases", [])
        bonuses = {}
        penalties = {}
        bonuses["evidence"] = {"high": 0.2, "medium": 0.1, "low": -0.25}.get(confidence, 0)
        bonuses["enterprise_case"] = min(0.25, 0.06 * len(matched_cases))
        bonuses["cross_validator_agreement"] = 0.15 if row["id"] in evaluator_top3 and row["id"] in validator_top3 else 0
        if approved_ids.get(row["id"]):
            bonuses["historical_human_approval"] = 0.2
        elif rejected_ids.get(row["id"]):
            bonuses["historical_human_approval"] = -0.2
        else:
            bonuses["historical_human_approval"] = 0
        penalties["governance_flags"] = 0.12 * len(flags)
        if any("High risk" in flag for flag in flags):
            penalties["risk_gate"] = 0.45
        else:
            penalties["risk_gate"] = 0
        if any("Low maturity" in flag for flag in flags):
            penalties["maturity_gate"] = 0.35
        else:
            penalties["maturity_gate"] = 0

        decision_score = round(row["average_score"] + sum(bonuses.values()) - sum(penalties.values()), 2)
        if flags and decision_score >= 3.0:
            recommended_action = "assess_with_human_review"
        elif decision_score >= 4.35:
            recommended_action = "adopt_candidate_after_review"
        elif decision_score >= 3.75:
            recommended_action = "trial_with_human_review"
        elif decision_score >= 3.0:
            recommended_action = "assess_watchlist"
        else:
            recommended_action = "hold"

        why = []
        if bonuses["cross_validator_agreement"]:
            why.append("evaluator and validator both placed this candidate in Top 3")
        if confidence == "high":
            why.append("high evidence confidence")
        if matched_cases:
            why.append(f"{len(matched_cases)} matched enterprise evidence item(s)")
        if not flags:
            why.append("no blocking governance flag")
        else:
            why.extend(flags[:3])
        if feedback_stats.get("sample_status") == "insufficient_for_ml_training":
            why.append("human feedback sample is still descriptive, not enough for ML training")

        decisions.append(
            {
                "id": row["id"],
                "title": row["title"],
                "average_score": row["average_score"],
                "decision_score": decision_score,
                "radar_ring": evidence.get("radar_ring", radar_ring(row)),
                "evidence_confidence": confidence,
                "recommended_action": recommended_action,
                "score_components": {
                    "base_average_score": row["average_score"],
                    "bonuses": bonuses,
                    "penalties": penalties,
                },
                "why": why,
            }
        )

    decisions.sort(key=lambda item: (-item["decision_score"], item["id"]))
    return {
        "decision_layer_version": "1.0",
        "run_id": run_id,
        "method": "interpretable weighted decision policy",
        "method_note": (
            "This is an explainable algorithmic decision layer, not a trained ML model. "
            "It combines evaluator/validator scores, evidence confidence, enterprise cases, governance flags, and available human feedback signals."
        ),
        "policy": {
            "base": "average evaluator/validator score",
            "positive_signals": ["evidence confidence", "enterprise case evidence", "evaluator-validator agreement", "historical human approval"],
            "negative_signals": ["governance flags", "high risk", "low maturity", "historical rejection"],
            "actions": ["adopt_candidate_after_review", "trial_with_human_review", "assess_with_human_review", "assess_watchlist", "hold"],
        },
        "top3": decisions[:3],
        "all_decisions": decisions,
    }


def build_audit_packet(run_id, keys, quote, rq2, agreement, evidence_ledger, review_packet, decision_layer, feedback_stats):
    top_actions = [item.get("recommended_action") for item in decision_layer.get("top3", [])]
    blocking_flags = [
        {"id": item["id"], "flags": item.get("rationale", {}).get("governance_flags", [])}
        for item in evidence_ledger.get("candidates", [])
        if item.get("rationale", {}).get("governance_flags")
    ]
    return {
        "audit_packet_version": "1.0",
        "run_id": run_id,
        "status": "awaiting_human_review",
        "trust_summary": {
            "quote_decision": quote.get("decision") if quote else None,
            "quoted_usd": quote.get("total_usd") if quote else None,
            "actual_llm_usd": rq2.get("quote", {}).get("actual_llm_usd"),
            "llm_tokens": rq2.get("tokens", {}),
            "top3_overlap": agreement.get("top3_overlap"),
            "feedback_sample_status": feedback_stats.get("sample_status"),
            "recommended_actions": top_actions,
        },
        "artifact_keys": keys,
        "checks": [
            {"name": "evidence_ledger_created", "passed": bool(keys.get("evidence_ledger_key"))},
            {"name": "review_packet_created", "passed": bool(keys.get("review_packet_key"))},
            {"name": "decision_layer_created", "passed": bool(keys.get("decision_layer_key"))},
            {"name": "feedback_stats_created", "passed": bool(keys.get("feedback_stats_key"))},
            {"name": "quote_gate_allows_run", "passed": quote.get("decision") == "approve" if quote else False},
            {"name": "human_review_pending", "passed": review_packet.get("status") == "awaiting_human_review"},
        ],
        "blocking_flags": blocking_flags,
        "next_actions": [
            "Record approve/reject/override/comment through recordhumanpick Lambda.",
            "Use feedback-stats.json after multiple days to quantify agreement and override trends.",
            "Treat decision-layer recommendations as explainable guidance until human review is complete.",
        ],
    }


def build_report(
    run_id,
    s1,
    s2,
    s3,
    s4,
    research=None,
    evidence_ledger=None,
    review_packet=None,
    decision_layer=None,
    feedback_stats=None,
    audit_packet=None,
):
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
    if evidence_ledger:
        evidence_rows = "".join(
            "<tr>"
            f"<td>{html.escape(c['id'])}</td>"
            f"<td>{html.escape(c['evidence_confidence'])}</td>"
            f"<td>{html.escape(c['radar_ring'])}</td>"
            f"<td>{html.escape('; '.join(c['rationale']['governance_flags']) or 'No blocking flag')}</td>"
            "</tr>"
            for c in evidence_ledger.get("candidates", [])[:6]
        )
        evidence_block = (
            "<h2>Evidence Ledger</h2>"
            "<p>Every candidate now carries an auditable chain from source article to L1 relevance, L2 evaluator score, independent validator score, governance flags, and final radar-ring recommendation.</p>"
            f"<table><tr><th>ID</th><th>Evidence</th><th>Ring</th><th>Governance flags</th></tr>{evidence_rows}</table>"
        )
    else:
        evidence_block = ""
    if review_packet:
        review_rows = "".join(
            "<tr>"
            f"<td>{item['rank']}</td>"
            f"<td>{html.escape(item['id'])}</td>"
            f"<td>{html.escape(item['title'])}</td>"
            f"<td>{item['average_score']}</td>"
            f"<td>{html.escape(item['radar_ring'])}</td>"
            "</tr>"
            for item in review_packet.get("ai_top3", [])
        )
        review_block = (
            "<h2>Human Review Gate</h2>"
            "<p>Status: <b>awaiting_human_review</b>. A reviewer should record approve, reject, override, or comment through the human-pick Lambda before this becomes an implementation recommendation.</p>"
            f"<table><tr><th>Rank</th><th>ID</th><th>Concept</th><th>Average</th><th>Ring</th></tr>{review_rows}</table>"
        )
    else:
        review_block = ""
    if decision_layer:
        decision_rows = "".join(
            "<tr>"
            f"<td>{html.escape(item['id'])}</td>"
            f"<td>{item['decision_score']}</td>"
            f"<td>{html.escape(item['recommended_action'])}</td>"
            f"<td>{html.escape('; '.join(item.get('why', [])[:3]))}</td>"
            "</tr>"
            for item in decision_layer.get("top3", [])
        )
        decision_block = (
            "<h2>Algorithmic Decision Layer</h2>"
            "<p>This layer applies an interpretable weighted decision policy above raw average score. It is not a trained ML model yet; human feedback logs are still being accumulated for future calibration.</p>"
            f"<table><tr><th>ID</th><th>Decision score</th><th>Recommended action</th><th>Why</th></tr>{decision_rows}</table>"
        )
    else:
        decision_block = ""
    if feedback_stats:
        counts = feedback_stats.get("counts", {})
        metrics = feedback_stats.get("metrics", {})
        feedback_block = (
            "<h2>Human Feedback Statistics</h2>"
            f"<p>Sample status: <b>{html.escape(str(feedback_stats.get('sample_status', 'unknown')))}</b>. "
            "These are descriptive statistics for now, not ML training evidence.</p>"
            "<table><tr><th>Metric</th><th>Value</th></tr>"
            f"<tr><td>AI pick logs</td><td>{counts.get('ai_pick_logs', 0)}</td></tr>"
            f"<tr><td>Human review logs</td><td>{counts.get('human_review_logs', 0)}</td></tr>"
            f"<tr><td>Approvals / rejections / overrides</td><td>{counts.get('approvals', 0)} / {counts.get('rejections', 0)} / {counts.get('overrides', 0)}</td></tr>"
            f"<tr><td>Average review minutes</td><td>{html.escape(str(metrics.get('average_human_review_minutes')))}</td></tr>"
            f"<tr><td>Average AI-human Top3 overlap</td><td>{html.escape(str(metrics.get('average_ai_human_top3_overlap')))}</td></tr>"
            "</table>"
        )
    else:
        feedback_block = ""
    if audit_packet:
        checks = "".join(
            f"<li>{html.escape(check['name'])}: {'PASS' if check.get('passed') else 'CHECK'}</li>"
            for check in audit_packet.get("checks", [])
        )
        audit_block = (
            "<h2>Audit Packet</h2>"
            "<p>The audit packet summarizes whether this run has the artifacts needed for governance review.</p>"
            f"<ul>{checks}</ul>"
        )
    else:
        audit_block = ""
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
  {decision_block}
  {evidence_block}
  {review_block}
  {feedback_block}
  {audit_block}
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
