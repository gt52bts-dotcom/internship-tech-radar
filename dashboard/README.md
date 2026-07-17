# Cleo 的 Skill 進度互動儀錶板

> 這份 dashboard 是 GitHub private repository 內的可攜式 Skill 進度資料。Notion 版本可嵌入 `cleo-skill-dashboard.html`，Git 版本則作為每日 17:00 AI PM 同步的 source of truth。

## 最新狀態

- 累積總分：105 分
- 最新日期：2026-07-17
- 今日重點：純 CloudFormation 公司帳戶部署成功，Step Functions `company-cfn-001` 端到端成功，並補上 evidence/review/decision/audit artifacts。

| Skill | 說明 | 累積分數 | 最新變化 |
|---|---|---:|---|
| Skill 1｜掃描 | 資料來源掃描、候選技術收集 | 15 | CloudFormation 版流程完成真實 RSS 掃描輸出。 |
| Skill 2｜比較 | 候選技術比較、案例對照 | 17 | S2 比較、Quote gate 與 Decision Layer 串接。 |
| Skill 3｜評估 | 評分邏輯、AHP/rubric/LLM 輔助評估 | 23 | 新增 Evidence Ledger、Human Review、Decision Layer、Feedback Stats 與 Audit Packet。 |
| Skill 4｜驗證 | 部署驗證、權限驗證、錯誤排查 | 26 | CloudFormation stack `CREATE_COMPLETE` 且 Step Functions `company-cfn-001` 成功。 |
| Skill 5｜報告 | Top 3 報告、HTML/文件輸出、週誌 | 24 | 新版報告 artifact、7 頁部會簡報與 AI 執行軌跡完成整理。 |

## 每日分數

| 日期 | 掃描 | 比較 | 評估 | 驗證 | 報告 | 每日總分 |
|---|---:|---:|---:|---:|---:|---:|
| 2026-07-13 | 4 | 4 | 4 | 4 | 5 | 21 |
| 2026-07-14 | 2 | 3 | 4 | 3 | 2 | 14 |
| 2026-07-15 | 2 | 2 | 2 | 3 | 5 | 14 |
| 2026-07-16 | 3 | 3 | 5 | 7 | 5 | 23 |
| 2026-07-17 | 4 | 5 | 8 | 9 | 7 | 33 |

## 檔案

- [互動儀錶板 HTML](./cleo-skill-dashboard.html)
- [Notion 可嵌入版 HTML](./notion-skill-dashboard.html)
- [Skill 分數資料 JSON](./skill-score-data.json)
- [完整 Skill 進度紀錄](../SKILL_PROGRESS.md)
- [專案首頁](../README.md)

## 17:00 同步規則

- 每個工作日 17:00 後才更新正式日誌與分數。
- 只登錄有證據的成果，例如 Step Functions 執行結果、S3 產出、DynamoDB 紀錄、Git diff、文件檔案。
- Notion 與 dashboard 若尚未完成同步，必須明確標示，不可假裝已同步。
