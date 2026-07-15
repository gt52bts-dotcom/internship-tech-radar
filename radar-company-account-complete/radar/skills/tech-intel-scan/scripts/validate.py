# -*- coding: utf-8 -*-
"""Step 4: 驗證（驗證者，模型 B）
獨立呼叫另一個 Anthropic 模型（預設 claude-haiku-4-5）作交叉檢核。
憲法：建造者不得驗證自己的產出——所以 --model 一定要跟 evaluate.py 不同。

用法：
  python validate.py --input s3_evaluate.json --output s4_validate.json \
                     --model claude-haiku-4-5
"""
import argparse
import json
import os
import sys

# 驗證者權重：與建造者刻意不同（五維均衡，偏保守）
WV = {"maturity": 0.20, "aws_fit": 0.20, "case_evidence": 0.20,
      "effort": 0.20, "risk": 0.20}


def v_score(sig):
    return round(
        sig["maturity"] * WV["maturity"]
        + sig["aws_fit"] * WV["aws_fit"]
        + sig.get("case_evidence", 2) * WV["case_evidence"]
        + (6 - sig["effort"]) * WV["effort"]
        + (6 - sig["risk"]) * WV["risk"], 2)


def hard_rules(article):
    """硬規則檢查。任何一條命中就標記為需人工複核。"""
    flags = []
    if article["signals"]["risk"] >= 4:
        flags.append("風險≥4：不得作為推薦首選")
    if article["signals"]["maturity"] <= 2:
        flags.append("成熟度≤2：僅能列入觀察（Assess），不宜 POC")
    return flags


def build_prompt(article, builder_sig):
    return f"""你是 Cathay Life 的獨立驗證員。建造者對以下文章給了評分，你需要用「不同角度」重新評分作為交叉檢核。

文章：
標題：{article['title']}
狀態：{article.get('status', 'unknown')}
摘要：{article['summary']}

建造者評分：{json.dumps(builder_sig, ensure_ascii=False)}
建造者理由：{article.get('llm_rationale', '')}

請以「更保守、更重視風險與導入成本」的角度重新給五維分數（1-5），不要盲目相信建造者：
{{"maturity": N, "aws_fit": N, "case_evidence": N, "effort": N, "risk": N, "verdict": "同意/不同意，一句話"}}
只輸出 JSON，不要 markdown 標記。"""


def validate_via_llm(article, builder_sig, model, client):
    try:
        response = client.messages.create(
            model=model, max_tokens=512,
            messages=[{"role": "user",
                       "content": build_prompt(article, builder_sig)}],
        )
        text = response.content[0].text.strip()
        text = text.lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(text)
    except Exception as e:
        print(f"  [WARN] 驗證者 LLM 呼叫失敗：{e}", file=sys.stderr)
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--model", default="claude-haiku-4-5")
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    use_api = not args.offline and bool(os.environ.get("ANTHROPIC_API_KEY"))
    client = None
    if use_api:
        try:
            import anthropic
            client = anthropic.Anthropic()
            mode = f"api.anthropic.com:{args.model}"
        except ImportError:
            use_api = False
    if not use_api:
        mode = "rubric（獨立第二權重）"

    print(f"[S4 驗證] 模式：{mode}")

    with open(args.input, encoding="utf-8") as f:
        s3 = json.load(f)
    builder_top3 = [t["id"] for t in s3["top3"]]

    rescored = []
    for a in s3["articles"]:
        if use_api:
            v_sig = validate_via_llm(a, a["signals"], args.model, client)
            score_sig = v_sig if v_sig else a["signals"]
        else:
            score_sig = a["signals"]
        rescored.append({
            "id": a["id"], "title": a["title"],
            "v_score": v_score(score_sig),
            "flags": hard_rules(a),
        })
    rescored.sort(key=lambda x: -x["v_score"])
    validator_top3 = [r["id"] for r in rescored[:3]]

    overlap = [i for i in builder_top3 if i in validator_top3]
    agreement = round(len(overlap) / 3, 2)
    disagreements = [
        {"id": i, "note": "建造者選入但驗證者未選入" if i in builder_top3 else "驗證者選入但建造者未選入"}
        for i in set(builder_top3) ^ set(validator_top3)]
    all_flags = [r for r in rescored if r["flags"]]
    verdict = "通過" if agreement >= 0.67 and not any(
        f["id"] in builder_top3 for f in all_flags) else "需人工複核"

    output = {
        "step": "s4_validate", "mode": mode,
        "validator_model": args.model if use_api else "rubric",
        "validator_weights": WV,
        "builder_top3": builder_top3, "validator_top3": validator_top3,
        "agreement_rate": agreement, "disagreements": disagreements,
        "hard_rule_flags": all_flags,
        "verdict": verdict, "rescored": rescored,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[S4 驗證] 一致率 {int(agreement*100)}% · 判定：{verdict}")
    if disagreements:
        for d in disagreements:
            print(f"        ↳ 分歧：{d['id']}（{d['note']}）")


if __name__ == "__main__":
    main()
