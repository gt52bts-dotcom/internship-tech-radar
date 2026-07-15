# -*- coding: utf-8 -*-
"""Step 3: 評估（建造者，模型 A）
呼叫 api.anthropic.com（**不透過 AWS Bedrock**）進行深度評估。
若無 ANTHROPIC_API_KEY 或 --offline 旗標，改用 rubric 計分。

用法：
  python evaluate.py --input s2_compare.json --cases case_studies/ \
                     --output s3_evaluate.json --model claude-sonnet-4-5
"""
import argparse
import json
import os
import sys
from pathlib import Path

# 建造者 rubric 權重 —— maturity 主權重反映主管「不要太新」原則
W = {"maturity": 0.35, "aws_fit": 0.25, "case_evidence": 0.15,
     "effort": 0.15, "risk": 0.10}


def load_case_studies(cases_dir: Path):
    """從資料夾載入所有案例 JSON。"""
    cases = []
    if not cases_dir.is_dir():
        return cases
    for fn in sorted(cases_dir.iterdir()):
        if fn.suffix == ".json":
            with open(fn, encoding="utf-8") as f:
                cases.append(json.load(f))
    return cases


def match_cases(article, cases):
    """對一篇文章找出相關案例：tags 與案例 matched_technologies 取交集。"""
    art_tags = set(article.get("tags", []))
    matched = []
    for c in cases:
        overlap = art_tags & set(c.get("matched_technologies", []))
        if overlap:
            matched.append({
                "id": c["id"],
                "customer": c["customer"],
                "overlap_tags": sorted(overlap),
                "relevance_to_cathay": c["relevance_to_cathay"]["score"],
            })
    matched.sort(key=lambda m: -m["relevance_to_cathay"])
    return matched


def case_evidence_score(matched):
    """案例證據分數（1-5）。無案例=2、有相關案例=3、有高相關案例=4-5。"""
    if not matched:
        return 2
    top = matched[0]["relevance_to_cathay"]
    count = len(matched)
    if count >= 2 and top >= 5: return 5
    if count >= 2 or top >= 5: return 4
    if top >= 4: return 4
    return 3


def composite(sig):
    """五維加權綜合分數。"""
    return round(
        sig["maturity"] * W["maturity"]
        + sig["aws_fit"] * W["aws_fit"]
        + sig["case_evidence"] * W["case_evidence"]
        + (6 - sig["effort"]) * W["effort"]
        + (6 - sig["risk"]) * W["risk"], 2)


def reason(article, matched):
    """自然語言的評估理由（給人看的）。"""
    s = article["signals"]
    parts = []
    if s["aws_fit"] >= 4: parts.append("與本組 AWS 技術棧高度契合")
    if s["maturity"] >= 4: parts.append("技術成熟度高、可直接 POC")
    if s["effort"] <= 2: parts.append("導入成本低")
    if s["risk"] >= 3: parts.append("⚠ 存在中度以上風險，需人工複核")
    if matched:
        top = matched[0]
        if top["relevance_to_cathay"] >= 5:
            parts.append(f"✓ 有高相關 enterprise 案例（{top['customer']}）")
        elif top["relevance_to_cathay"] >= 4:
            parts.append(f"有 enterprise 案例（{top['customer']}）")
        if len(matched) >= 2:
            parts.append(f"共 {len(matched)} 個相關案例可對照")
    else:
        parts.append("⚠ 尚無 enterprise 案例可對照")
    return "；".join(parts) or "綜合分數達標"


def build_prompt(article, matched_cases):
    """建構給 LLM 的評估提示詞。回傳嚴格 JSON。"""
    cases_txt = "\n".join([
        f"- {m['customer']}（相關性 {m['relevance_to_cathay']}/5，共通標籤：{'、'.join(m['overlap_tags'])}）"
        for m in matched_cases[:5]]) or "（無相關案例）"
    return f"""你是 Cathay Life（台灣人壽保險業）的技術評估員。請對以下技術文章進行深度評估。

文章：
標題：{article['title']}
來源：{article['source']}
摘要：{article['summary']}
狀態：{article.get('status', 'unknown')}
GA 日期：{article.get('ga_date', 'unknown')}
標籤：{'、'.join(article.get('tags', []))}

Cathay 相關 enterprise 案例可對照：
{cases_txt}

請針對以下 5 個維度各給 1-5 分並簡短說明。**評估原則**：
- Preview / Beta 一律不超過 2 分
- 剛 GA (<3 個月) 最高 3 分
- 保險業對合規、資料主權特別敏感，這方面 risk 要保守
- Cathay 已鎖定 AWS，非 AWS 技術 aws_fit 最高 3 分

輸出嚴格 JSON（不要 markdown 標記）：
{{"maturity": N, "aws_fit": N, "case_evidence": N, "effort": N, "risk": N, "rationale": "一句話總結"}}
"""


def evaluate_via_llm(article, matched_cases, model, client):
    """呼叫 Anthropic API 取得五維評分。失敗時回傳 None 讓上層 fallback。"""
    try:
        response = client.messages.create(
            model=model,
            max_tokens=512,
            messages=[{"role": "user",
                       "content": build_prompt(article, matched_cases)}],
        )
        text = response.content[0].text.strip()
        # 保險：LLM 有時會加 markdown 標記，去掉
        text = text.lstrip("```json").lstrip("```").rstrip("```").strip()
        sig = json.loads(text)
        return ({k: int(sig[k]) for k in
                 ["maturity", "aws_fit", "case_evidence", "effort", "risk"]},
                sig.get("rationale", ""))
    except Exception as e:
        print(f"  [WARN] LLM 呼叫失敗：{e}，此篇 fallback 到 rubric", file=sys.stderr)
        return None


def evaluate_via_rubric(article, matched_cases):
    """rubric 計分：不呼叫 API，用文章的內建 signals + 案例證據。"""
    sig = dict(article["signals"])
    sig["case_evidence"] = case_evidence_score(matched_cases)
    return sig, "(rubric mode)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="s2_compare.json 路徑")
    ap.add_argument("--cases", required=True, help="case_studies 資料夾路徑")
    ap.add_argument("--output", required=True, help="輸出 s3_evaluate.json 路徑")
    ap.add_argument("--model", default="claude-sonnet-4-5",
                    help="Anthropic 模型 ID")
    ap.add_argument("--offline", action="store_true",
                    help="強制 rubric 模式（不呼叫 API）")
    args = ap.parse_args()

    # 決定執行模式
    use_api = not args.offline and bool(os.environ.get("ANTHROPIC_API_KEY"))
    client = None
    if use_api:
        try:
            import anthropic
            client = anthropic.Anthropic()  # 自動讀 ANTHROPIC_API_KEY
            mode = f"api.anthropic.com:{args.model}"
        except ImportError:
            print("[WARN] anthropic 套件未安裝，改用 rubric", file=sys.stderr)
            use_api = False
    if not use_api:
        mode = "rubric（本地，不呼叫 API）"

    print(f"[S3 評估] 模式：{mode}")

    # 載入輸入
    with open(args.input, encoding="utf-8") as f:
        s2 = json.load(f)
    cases = load_case_studies(Path(args.cases))
    print(f"        載入 {len(cases)} 個 enterprise 案例")

    # 逐篇評估
    evaluated = []
    for a in s2["articles"]:
        a3 = dict(a)
        matched = match_cases(a, cases)
        a3["matched_cases"] = matched
        # 呼叫 API 或走 rubric
        result = evaluate_via_llm(a, matched, args.model, client) if use_api else None
        if result is None:
            result = evaluate_via_rubric(a, matched)
        sig, note = result
        a3["signals"] = sig
        a3["llm_rationale"] = note
        a3["l2_score"] = composite(sig)
        a3["reason"] = reason(a3, matched)
        evaluated.append(a3)
    evaluated.sort(key=lambda x: -x["l2_score"])
    top3 = evaluated[:3]

    output = {
        "step": "s3_evaluate", "mode": mode,
        "evaluator_model": args.model if use_api else "rubric",
        "rubric_weights": W,
        "case_studies_loaded": len(cases),
        "case_studies_ids": [c["id"] for c in cases],
        "input_count": len(evaluated),
        "top3": [{"id": t["id"], "title": t["title"], "l2_score": t["l2_score"],
                  "reason": t["reason"], "matched_cases": t["matched_cases"]}
                 for t in top3],
        "articles": evaluated,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[S3 評估] Top-3：{[t['id'] for t in top3]}")
    for t in top3:
        n = len(t["matched_cases"])
        print(f"        · {t['id']} L2={t['l2_score']}，引用 {n} 案例")


if __name__ == "__main__":
    main()
