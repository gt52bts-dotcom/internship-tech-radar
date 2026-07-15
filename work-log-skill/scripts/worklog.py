# -*- coding: utf-8 -*-
"""Generate internship work logs and evidence lists.

Examples:
  python scripts/worklog.py draft --date 2026-07-14 --project "Cathay Tech Intel v3" --done "補齊 CDK"
  python scripts/worklog.py scan --root . --days 2
  python scripts/worklog.py weekly --logs logs --output weekly-summary.md
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path


def as_list(values):
    return values or []


def bullets(values, empty="無"):
    values = as_list(values)
    if not values:
        return f"- {empty}"
    return "\n".join(f"- {value}" for value in values)


def write_or_print(text, output):
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(path)
    else:
        print(text)


def cmd_draft(args):
    date = args.date or datetime.now().strftime("%Y-%m-%d")
    title = f"# 工作日誌 - {date}"
    if args.project:
        title += f"\n\n專案：{args.project}"
    conclusion = args.conclusion or "完成今日主要工作，並整理驗證結果與下一步。"
    text = f"""{title}

## 今日主題

{conclusion}

## 今日完成事項

{bullets(args.done)}

## 執行驗證

{bullets(as_list(args.verify) + as_list(args.evidence))}

## 當日流程圖

```mermaid
flowchart LR
    A[開始] --> B[今日主要工作]
    B --> C[驗證結果]
    C --> D[完成或待處理]
```

## Mentor 討論筆記

### 第一次討論

- 關鍵字：
- 小筆記：

### 第二次討論

- 關鍵字：
- 小筆記：

## 遇到的問題與處理

{bullets(args.blocker)}

## 技術調整紀錄

{bullets(args.decision)}

## 提醒事項

{bullets(as_list(args.next) + as_list(args.ask))}

## 今日總結

{conclusion}
"""
    write_or_print(text, args.output)


def cmd_scan(args):
    root = Path(args.root).resolve()
    cutoff = datetime.now() - timedelta(days=args.days)
    rows = []
    patterns = {".zip", ".md", ".html", ".py", ".json", ".yaml", ".yml", ".ps1", ".sh"}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {"__pycache__", ".git"} for part in path.parts):
            continue
        if path.suffix.lower() not in patterns:
            continue
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        if mtime < cutoff:
            continue
        rows.append({
            "path": str(path),
            "size": path.stat().st_size,
            "modified": mtime.strftime("%Y-%m-%d %H:%M:%S"),
        })
    rows.sort(key=lambda item: item["modified"], reverse=True)
    if args.json:
        write_or_print(json.dumps(rows, ensure_ascii=False, indent=2), args.output)
        return
    text = "\n".join(f"- `{row['path']}` ({row['modified']}, {row['size']} bytes)" for row in rows) or "- 無近期證據檔案"
    write_or_print(text, args.output)


def cmd_weekly(args):
    logs_dir = Path(args.logs)
    files = sorted(logs_dir.glob("*.md"))
    sections = []
    for file in files:
        body = file.read_text(encoding="utf-8")
        first_lines = "\n".join(body.splitlines()[:12])
        sections.append(f"## {file.stem}\n\n{first_lines}")
    text = f"""# 週報彙整

## 本週總結

本週共彙整 {len(files)} 份工作日誌。請依主管需求補上最終結論。

## 每日摘要

{chr(10).join(sections) if sections else '尚未找到日誌檔案。'}
"""
    write_or_print(text, args.output)


def cmd_biweekly(args):
    logs_dir = Path(args.logs)
    files = sorted(logs_dir.glob("*.md"))
    evidence = []
    for file in files:
        body = file.read_text(encoding="utf-8")
        evidence.append(f"- `{file.name}`：請擷取其中可證明成果、決策或成長的內容。")
    text = f"""# 雙週誌

## 本期一句話總結

請用一句話統整最重要的成果、價值與目前狀態；不要逐日敘述。

## 核心成果與影響

- 成果：
  - 影響：
  - 證據：

## 關鍵問題與解法

- 問題與限制：
- 判斷與解法：
- 結果或待驗證事項：

## 學習與能力成長

- 原本：
- 公司提供的支持：
- 現在能做到：
- 成長證據：

## 下期重點

- 預期成果一：
- 預期成果二：

## 來源日誌（僅供整理，不直接貼入雙週誌）

{chr(10).join(evidence) if evidence else '- 尚未找到日誌檔案。'}
"""
    write_or_print(text, args.output)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(required=True)

    draft = sub.add_parser("draft")
    draft.add_argument("--date")
    draft.add_argument("--project")
    draft.add_argument("--conclusion")
    draft.add_argument("--done", action="append")
    draft.add_argument("--decision", action="append")
    draft.add_argument("--evidence", action="append")
    draft.add_argument("--verify", action="append")
    draft.add_argument("--blocker", action="append")
    draft.add_argument("--next", action="append")
    draft.add_argument("--ask", action="append")
    draft.add_argument("--output")
    draft.set_defaults(func=cmd_draft)

    scan = sub.add_parser("scan")
    scan.add_argument("--root", default=".")
    scan.add_argument("--days", type=int, default=2)
    scan.add_argument("--json", action="store_true")
    scan.add_argument("--output")
    scan.set_defaults(func=cmd_scan)

    weekly = sub.add_parser("weekly")
    weekly.add_argument("--logs", required=True)
    weekly.add_argument("--output")
    weekly.set_defaults(func=cmd_weekly)

    biweekly = sub.add_parser("biweekly")
    biweekly.add_argument("--logs", required=True)
    biweekly.add_argument("--output")
    biweekly.set_defaults(func=cmd_biweekly)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
