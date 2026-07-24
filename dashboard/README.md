# Cleo Skill 積分儀表板

> GitHub 是專案 source of truth。此頁整理主管可讀入口、五個 Skill 累積分數與每日趨勢；正式日誌仍以 `logs/daily/` 為準。

## 主管快速入口

| 入口 | 說明 |
|---|---|
| [查看評分表集合](../evaluation-forms/README.md) | 集中查看國泰評分表、Mentor 觀察表與海大實習表單。 |
| [主管評分自評儀表板（Notion）](https://app.notion.com/p/3a49d9fba316816c8f95d2a2ff997350) | 主管可快速查看自評摘要與每日更新規則。 |
| [主管評分表細則與回覆（Notion）](https://app.notion.com/p/3a49d9fba316814e923ad82718952a71) | Notion 版主管評分細則頁。 |
| [Mentor 評分細則](./mentor-evaluation-details.md) | 依證據整理四大項目與 Mentor 15 項觀察。 |

目前主管評分建議：四大項目平均 `4.5 / 5`；AI 模擬 Mentor 15 項平均 `4.40 / 5`。正式分數仍以 mentor 最終填寫為準。

## 累積分數

截至 2026-07-23，嚴格審核後累積總分為 `66`。每日總分最高 10 分，舊版 107 分不再作為正式累積值。

| Skill | 累積分數 | 狀態 |
|---|---:|---|
| Skill 1 - Scan | 10 | 已能從 AWS 新聞、官方文件與帳號資源盤點抽出可驗證候選。 |
| Skill 2 - Compare | 10 | 已能比較替代技術、部署方式與適用限制。 |
| Skill 3 - Evaluate | 14 | 已把成本、權限、安全、fallback 與 cleanup 納入判斷。 |
| Skill 4 - Validate | 21 | 已完成多次 CLI / CloudFormation / AWS 實機 PoC，並開始補 Console 人工確認與 cleanup 回驗。 |
| Skill 5 - Report | 11 | 已能產出教學書、報告、證據包與主管可讀入口。 |

## 每日趨勢

| 日期 | Scan | Compare | Evaluate | Validate | Report | 當日總分 |
|---|---:|---:|---:|---:|---:|---:|
| 2026-07-13 | 1 | 2 | 1 | 3 | 1 | 8 |
| 2026-07-14 | 1 | 1 | 1 | 2 | 1 | 6 |
| 2026-07-15 | 1 | 1 | 1 | 1 | 1 | 5 |
| 2026-07-16 | 1 | 1 | 2 | 3 | 1 | 8 |
| 2026-07-17 | 1 | 1 | 2 | 4 | 2 | 10 |
| 2026-07-20 | 2 | 1 | 2 | 1 | 1 | 7 |
| 2026-07-21 | 1 | 1 | 2 | 4 | 1 | 9 |
| 2026-07-22 | 1 | 1 | 2 | 2 | 2 | 8 |
| 2026-07-23 | 1 | 1 | 1 | 1 | 1 | 5 |

## 今日判定

2026-07-23 的核心成果是把指定 S3 Files 新聞完整跑過 S1–S5，釐清外部 LLM fallback 原因，並開始整理 AI PM 科會簡報。今日依使用者回饋下修為 `+5`；既有 PoC 雙向檔案回查、展示型 GUI 與截圖補證據不再列為 Cleo 當天個人日誌核心成果。

## 相關檔案

- [正式日誌](../logs/daily/work-log-2026-07-23.md)
- [Skill 積分明細](../SKILL_PROGRESS.md)
- [Skill JSON 資料](./skill-score-data.json)
- [互動式 Skill dashboard](./cleo-skill-dashboard.html)
- [Notion 內嵌 dashboard](./notion-skill-dashboard.html)
- [專案首頁](../README.md)

## 待修正流程

- S3 Files 指定新聞仍待有效 API key 重跑、真人核准紀錄與 cleanup；既有 PoC 補證據不列為個人日誌核心成果。
- `cdk deploy` 仍受 bootstrap role 權限限制，目前以 `cdk synth` 加 CloudFormation deploy 作為替代路徑。
