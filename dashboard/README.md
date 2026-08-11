# Cleo Skill 積分儀表板

> GitHub 是專案共同紀錄來源。此頁整理主管可讀入口、五個 Skill 累積分數與每日趨勢；正式日誌仍以每日工作日誌為準。

## 主管快速入口

| 入口 | 說明 |
|---|---|
| [查看評分表集合](../evaluation-forms/README.md) | 集中查看國泰評分表、Mentor 觀察表與海大實習表單。 |
| [主管評分自評儀表板（Notion）](https://app.notion.com/p/3a49d9fba316816c8f95d2a2ff997350) | 主管可快速查看自評摘要與每日更新規則。 |
| [主管評分表細則與回覆（Notion）](https://app.notion.com/p/3a49d9fba316814e923ad82718952a71) | Notion 版主管評分細則頁。 |
| [Mentor 評分細則](./mentor-evaluation-details.md) | 依證據整理四大項目與 Mentor 15 項觀察。 |

目前主管評分建議：四大項目平均 `4.5 / 5`；AI 模擬 Mentor 15 項平均 `4.40 / 5`。正式分數仍以 mentor 最終填寫為準。

## 累積分數

截至 2026-08-11，嚴格審核後累積總分為 `162`。8/11 完成三案 Skill 1 精準計時、四案例時間口徑校正與協理報告素材；未建立 AWS 資源。每日總分最高 10 分。

| Skill | 累積分數 | 狀態 |
|---|---:|---|
| Skill 1 - Scan | 26 | 已能以 AWS 官方 URL、RSS、動態分類、正式發布證據與新聞解釋層取得可驗證候選。 |
| Skill 2 - Compare | 24 | 已能用官方補充來源比較候選、部署前提與適用限制。 |
| Skill 3 - Evaluate | 34 | 已把成本、權限、安全、PoC proof question 與五構面通用 rubric 納入判斷。 |
| Skill 4 - Validate | 46 | 已完成多次 CLI / CloudFormation / AWS 實機 PoC，並補上 recipe、成本模型、資源盤點與清除規則。 |
| Skill 5 - Report | 32 | 已能產出結案／階段性報告、成本邊界、交接包與主管可讀成果提案素材。 |

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
| 2026-08-03 | 2 | 1 | 2 | 3 | 2 | 10 |
| 2026-08-04 | 2 | 2 | 2 | 0 | 2 | 8 |
| 2026-08-05 | 0 | 0 | 4 | 2 | 2 | 8 |
| 2026-08-11 | 2 | 2 | 1 | 2 | 2 | 9 |
| **2026-08-11 累積** | **26** | **24** | **34** | **46** | **32** | **162** |

## 今日判定

2026-08-11 的可計分成果是三案 Skill 1 精準計時、四案例時間口徑校正、停止案例規則與協理報告素材；累積分數為 162。沒有新增 AWS 資源、live PoC、帳務或 Mentor 回饋證據。

## 相關檔案

- [最新正式日誌](../logs/daily/work-log-2026-08-11.md)
- [8/5 校正日誌](../logs/daily/work-log-2026-08-05.md)
- [8/4 正式日誌](../logs/daily/work-log-2026-08-04.md)
- [Skill 積分明細](../SKILL_PROGRESS.md)
- [Skill JSON 資料](./skill-score-data.json)
- [互動式 Skill dashboard](./cleo-skill-dashboard.html)
- [Notion 內嵌 dashboard](./notion-skill-dashboard.html)
- [專案首頁](../README.md)

## 待修正流程

- Amazon Connect Customer Data Lake 若要進入真實 PoC，仍須補齊候選專屬 recipe、rate card、新加坡可用性／定價證據、可用 instance 與具名授權。
- 公開牌價報價與清除前執行紀錄不等於 AWS 實際帳務成本；Skill 5 不做未取得帳務資料的實際成本比較。
- `cdk deploy` 仍受 bootstrap role 權限限制；目前以 `cdk synth` 加 CloudFormation deploy 作為替代路徑，這不代表 CDK bootstrap 部署已成功。
