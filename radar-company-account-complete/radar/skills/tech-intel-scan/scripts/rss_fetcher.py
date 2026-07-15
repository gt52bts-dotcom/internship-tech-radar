# -*- coding: utf-8 -*-
"""Step 1: 掃描
從 sources.json 定義的 RSS 端點抓文章，自動推論 tags/status/signals，
執行 L0 規則過濾（Preview/Beta 直擋、無關鍵字直擋、超過 14 天直擋、重複標題直擋）。

用法：
  python rss_fetcher.py --sources data/sources.json --output out/s1_scan.json
  python rss_fetcher.py --use-fixtures --fixtures data/fixtures.json --output out/s1_scan.json
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime
from email.utils import parsedate_to_datetime

NEEDS_KEYWORDS = {
    "bedrock": 3.0, "agent": 2.5, "stepfunctions": 2.0, "orchestration": 2.0,
    "evaluation": 2.0, "validation": 2.0, "rag": 1.5, "embedding": 1.5,
    "vector": 1.5, "eventbridge": 1.5, "llm": 1.0, "nova": 1.0,
    "knowledge-base": 1.5, "hitl": 1.5, "llm-judge": 2.0, "batch": 1.0,
    "scheduler": 0.5, "cost": 0.5, "guardrails": 2.0, "compliance": 1.5,
    "best-practice": 1.0, "migration": 1.0, "backup": 0.5, "disaster-recovery": 0.5,
}

TAG_KEYWORDS = [
    ("bedrock",         [r"\bbedrock\b", r"amazon bedrock"]),
    ("agent",           [r"\bagent(s|core)?\b", r"multi-?agent"]),
    ("nova",            [r"\bnova\b", r"amazon nova"]),
    ("guardrails",      [r"\bguardrails?\b"]),
    ("knowledge-base",  [r"knowledge base", r"\bkb\b"]),
    ("rag",             [r"\brag\b", r"retrieval augment"]),
    ("vector",          [r"\bvector\b", r"embedding"]),
    ("llm-judge",       [r"llm[- ]as[- ]a[- ]judge"]),
    ("evaluation",      [r"\beval(uation|s)?\b"]),
    ("stepfunctions",   [r"step functions?", r"state machine"]),
    ("eventbridge",     [r"eventbridge"]),
    ("scheduler",       [r"scheduler"]),
    ("orchestration",   [r"orchestrat"]),
    ("compliance",      [r"compliance", r"fedramp", r"hipaa"]),
    ("migration",       [r"\bmigrat", r"\brehost\b"]),
    ("backup",          [r"\bbackup\b"]),
    ("disaster-recovery", [r"disaster recovery"]),
    ("cost",            [r"\bcost\b", r"pricing", r"price cut"]),
    ("best-practice",   [r"best practice"]),
    ("batch",           [r"\bbatch\b"]),
    ("hitl",            [r"human[- ]in[- ]the[- ]loop"]),
    ("llm",             [r"\bllm\b", r"foundation model", r"large language model"]),
]

STATUS_PATTERNS = [
    ("Preview", [r"\bpublic preview\b", r"\bpreview\b", r"in preview"]),
    ("Beta",    [r"\bbeta\b"]),
    ("GA",      [r"\bga\b", r"generally available", r"now available"]),
]

MAX_AGE_DAYS = 14


def strip_html(html):
    if not html: return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def infer_tags(text):
    tags = []
    for tag, patterns in TAG_KEYWORDS:
        if any(re.search(p, text, re.IGNORECASE) for p in patterns):
            tags.append(tag)
    return tags


def infer_status(text):
    for status, patterns in STATUS_PATTERNS:
        if any(re.search(p, text, re.IGNORECASE) for p in patterns):
            return status
    return "unknown"


def infer_signals(text, cloud, status):
    t = text.lower()
    if status == "Preview": maturity = 1
    elif status == "Beta": maturity = 2
    elif re.search(r"just (announced|released|launched)", t): maturity = 3
    elif status == "GA": maturity = 4
    else: maturity = 3
    aws_fit = {"aws": 5, "gcp": 3, "azure": 3}.get(cloud, 2)
    if re.search(r"one[- ]click|no[- ]code|managed|instant", t): effort = 2
    elif re.search(r"migrat|refactor|rewrite", t): effort = 4
    else: effort = 3
    if status == "Preview": risk = 4
    elif status == "Beta": risk = 3
    elif re.search(r"deprecat|legacy", t): risk = 5
    elif status == "GA": risk = 2
    else: risk = 3
    return {"maturity": maturity, "aws_fit": aws_fit, "effort": effort, "risk": risk}


def parse_date(entry):
    for k in ("published", "updated", "created"):
        if hasattr(entry, k):
            try:
                return parsedate_to_datetime(getattr(entry, k)).strftime("%Y-%m-%d")
            except Exception: pass
    return date.today().strftime("%Y-%m-%d")


def make_id(url):
    return "R-" + hashlib.md5(url.encode()).hexdigest()[:8].upper()


def normalize_entry(entry, source):
    title = entry.get("title", "").strip()
    summary = strip_html(entry.get("summary", ""))[:500]
    url = entry.get("link", "")
    if not (title and url): return None
    full = title + " " + summary
    tags = infer_tags(full)
    if not tags: return None
    status = infer_status(full)
    signals = infer_signals(full, source["cloud"], status)
    return {
        "id": make_id(url), "title": title,
        "source": source["name"], "date": parse_date(entry),
        "url": url, "summary": summary or title,
        "cloud": source["cloud"], "tags": tags, "status": status,
        "ga_date": None, "signals": signals, "_inferred": True,
    }


def fetch_rss(sources_config):
    """從 RSS 抓取，回傳 (articles, fetch_log)。"""
    try:
        import feedparser
    except ImportError:
        raise RuntimeError("feedparser 未安裝：pip install feedparser")

    articles, log, seen_urls, seen_titles = [], [], set(), set()
    for src in sources_config.get("sources", []):
        if not src.get("enabled"): continue
        entry_count, kept, err = 0, 0, None
        try:
            feed = feedparser.parse(src["url"])
            for entry in feed.entries[:src.get("max_items", 10)]:
                entry_count += 1
                a = normalize_entry(entry, src)
                if a is None: continue
                if a["url"] in seen_urls: continue
                title_key = a["title"].lower().strip()[:80]
                if title_key in seen_titles: continue
                seen_urls.add(a["url"])
                seen_titles.add(title_key)
                articles.append(a)
                kept += 1
        except Exception as e:
            err = str(e)
        log.append({"source": src["name"], "raw_entries": entry_count,
                    "kept": kept, "error": err})
    return articles, log


def apply_l0(articles, today):
    """L0 規則過濾。"""
    kept, dropped, seen = [], [], set()
    for a in articles:
        reason = None
        h = hashlib.md5(a["title"].strip().encode()).hexdigest()[:10]
        try:
            age = (today - date.fromisoformat(a["date"])).days
        except Exception:
            age = 0
        status = a.get("status", "").lower()
        if not any(t in NEEDS_KEYWORDS for t in a.get("tags", [])):
            reason = "L0：無雲端/AI 相關關鍵字"
        elif "preview" in status or "beta" in status:
            reason = f"L0：狀態為 {a.get('status')}，未 GA 不推薦企業導入"
        elif age > MAX_AGE_DAYS:
            reason = f"L0：超過 {MAX_AGE_DAYS} 天（{age} 天前）"
        elif h in seen:
            reason = "L0：標題重複（轉載）"
        if reason:
            dropped.append({"id": a["id"], "title": a["title"], "reason": reason})
        else:
            seen.add(h)
            kept.append(a)
    return kept, dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", help="sources.json 路徑（RSS 模式）")
    ap.add_argument("--use-fixtures", action="store_true", help="改用 fixtures")
    ap.add_argument("--fixtures", help="fixtures.json 路徑")
    ap.add_argument("--output", required=True)
    ap.add_argument("--today", default=str(date.today()), help="YYYY-MM-DD")
    args = ap.parse_args()

    today = date.fromisoformat(args.today)
    fetch_log = []

    if args.use_fixtures or not args.sources:
        with open(args.fixtures or "data/fixtures.json", encoding="utf-8") as f:
            raw = json.load(f)
        source_mode = "fixtures"
        print(f"[S1] 使用 fixtures：{len(raw)} 篇")
    else:
        with open(args.sources, encoding="utf-8") as f:
            sources = json.load(f)
        try:
            raw, fetch_log = fetch_rss(sources)
            source_mode = "rss"
            print(f"[S1] RSS 抓到 {len(raw)} 篇")
        except Exception as e:
            print(f"[S1] RSS 失敗 fallback 到 fixtures：{e}", file=sys.stderr)
            with open(args.fixtures or "data/fixtures.json", encoding="utf-8") as f:
                raw = json.load(f)
            source_mode = "fixtures-fallback"

    kept, dropped = apply_l0(raw, today)
    output = {
        "step": "s1_scan", "source_mode": source_mode,
        "fetch_log": fetch_log,
        "input_count": len(raw), "kept_count": len(kept),
        "dropped": dropped, "articles": kept,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[S1] {len(raw)} → {len(kept)} 篇（過濾 {len(dropped)}）")


if __name__ == "__main__":
    main()
