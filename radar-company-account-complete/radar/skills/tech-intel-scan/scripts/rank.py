# -*- coding: utf-8 -*-
"""Step 2: 比對（L1 粗排 + 跨雲對應）
用需求關鍵字加權排序 → 取 Top-K 進入 L2。"""
import argparse
import json

NEEDS_KEYWORDS = {
    "bedrock": 3.0, "agent": 2.5, "stepfunctions": 2.0, "orchestration": 2.0,
    "evaluation": 2.0, "validation": 2.0, "rag": 1.5, "embedding": 1.5,
    "vector": 1.5, "eventbridge": 1.5, "llm": 1.0, "nova": 1.0,
    "knowledge-base": 1.5, "hitl": 1.5, "llm-judge": 2.0, "batch": 1.0,
    "scheduler": 0.5, "cost": 0.5, "guardrails": 2.0, "compliance": 1.5,
    "best-practice": 1.0, "migration": 1.0, "backup": 0.5,
}

CROSS_CLOUD_MAP = {
    "agent":      {"aws": "Bedrock AgentCore", "gcp": "Vertex AI Agent Builder", "azure": "AI Foundry Agents"},
    "evaluation": {"aws": "Bedrock Evaluations", "gcp": "Vertex Gen AI Evaluation", "azure": "Foundry Agent Eval"},
    "rag":        {"aws": "Bedrock Knowledge Bases", "gcp": "Vertex AI Search", "azure": "AI Search"},
    "vector":     {"aws": "S3 Vectors / OpenSearch", "gcp": "Vertex Vector Search", "azure": "AI Search vectors"},
}


def relevance(article):
    return round(sum(NEEDS_KEYWORDS.get(t, 0) for t in article["tags"]), 2)


def cross_cloud(article):
    return [{"能力": t, **CROSS_CLOUD_MAP[t]} for t in article["tags"] if t in CROSS_CLOUD_MAP]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--top-k", type=int, default=6)
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        s1 = json.load(f)
    scored = []
    for a in s1["articles"]:
        a2 = dict(a)
        a2["l1_score"] = relevance(a)
        a2["cross_cloud"] = cross_cloud(a)
        scored.append(a2)
    scored.sort(key=lambda x: -x["l1_score"])
    kept, cut = scored[:args.top_k], scored[args.top_k:]

    output = {
        "step": "s2_compare", "input_count": len(scored),
        "kept_count": len(kept),
        "cut": [{"id": c["id"], "title": c["title"], "l1_score": c["l1_score"]} for c in cut],
        "articles": kept,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[S2] 粗排 {len(scored)} → Top-{args.top_k}")


if __name__ == "__main__":
    main()
