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

截至 2026-08-03，嚴格審核後累積總分為 `127`。每日總分最高 10 分。

| Skill | 累積分數 | 狀態 |
|---|---:|---|
| Skill 1 - Scan | 20 | 已能以 AWS 官方 URL、RSS、動態分類與 GA 證據取得可驗證候選。 |
| Skill 2 - Compare | 18 | 已能用官方補充來源比較候選、部署前提與適用限制。 |
| Skill 3 - Evaluate | 24 | 已把成本、權限、安全、GA 證據、架構圖與 cleanup 前決策納入判斷。 |
| Skill 4 - Validate | 41 | 已完成多次 CLI / CloudFormation / AWS 實機 PoC，並完成 approval、resource inventory review 與 cleanup 契約硬化。 |
| Skill 5 - Report | 24 | 已能產出 artifact-only final／interim report、成本邊界、資源盤點、交接包與主管可讀入口。 |

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
| 2026-07-24 | 0 | 0 | 1 | 0 | 3 | 4 |
| 2026-07-27 | 2 | 1 | 1 | 3 | 2 | 9 |
| 2026-07-28 | 3 | 2 | 1 | 1 | 1 | 8 |
| 2026-07-29 | 2 | 2 | 1 | 4 | 1 | 10 |
| 2026-07-30 | 1 | 1 | 2 | 4 | 2 | 10 |
| 2026-07-31 | 1 | 1 | 2 | 4 | 2 | 10 |
| 2026-08-03 | 1 | 1 | 2 | 4 | 2 | 10 |
| **2026-08-03 累積** | **20** | **18** | **24** | **41** | **24** | **127** |

## 今日判定

2026-08-03 的核心成果是完成 Lambda 與 S3 Files 兩條 AWS 官方案例的 S1-S5 final 證據鏈，並將 Skill 4 close gate 從截圖 metadata 強化為 structured resource inventory、報價對照與權限面盤點。S3 Files 本次 PoC 已完成部署、雙向同步驗證、cleanup 前用量快照、run-scoped cleanup 與 Skill 5 final；公開牌價估算仍不等於 AWS 帳務成本。

## 相關檔案

- [正式日誌](../logs/daily/work-log-2026-08-03.md)
- [Skill 積分明細](../SKILL_PROGRESS.md)
- [Skill JSON 資料](./skill-score-data.json)
- [互動式 Skill dashboard](./cleo-skill-dashboard.html)
- [Notion 內嵌 dashboard](./notion-skill-dashboard.html)
- [專案首頁](../README.md)

## 待修正流程

- Amazon Connect Customer Data Lake 若要進入真實 PoC，仍須補齊候選專屬 recipe、rate card、新加坡可用性／定價證據、可用 instance 與具名授權。
- 公開牌價報價與 cleanup 前 runtime facts 不等於 AWS Billing / Cost Explorer / CUR 帳務成本；Skill 5 不做未取得帳務資料的實際成本比較。
- `cdk deploy` 仍受 bootstrap role 權限限制；目前以 `cdk synth` 加 CloudFormation deploy 作為替代路徑，這不代表 CDK bootstrap 部署已成功。
