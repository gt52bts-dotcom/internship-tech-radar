# Cleo 的 Skill 進度互動儀錶板

> 這份 dashboard 是 GitHub private repository 內的可攜式 Skill 進度資料。Notion 版本可嵌入 `cleo-skill-dashboard.html`，Git 版本則作為每日 17:00 AI PM 同步的 source of truth。

## 最新狀態

- 累積總分：134 分
- 最新日期：2026-07-20
- 今日重點：整理 final proposal/demo 素材，完成 S3 Files 新聞截斷評估、CLI 教學書與兩份 CloudFormation template validation；保單穩定性 PoC 保留為支援素材。

| Skill | 說明 | 累積分數 | 最新變化 |
|---|---|---:|---|
| Skill 1｜掃描 | 資料來源掃描、候選技術收集 | 21 | 完成 AWS 候選、保單穩定性與 S3 Files 官方資料掃描，並排除近期不採用的 Bedrock 路線。 |
| Skill 2｜比較 | 候選技術比較、案例對照 | 21 | 完成保單穩定性候選比較，並把 S3 Files 新聞轉成可驗證實作路線。 |
| Skill 3｜評估 | 評分邏輯、AHP/rubric/LLM 輔助評估 | 29 | 完成 CloudWatch Synthetics 報價、S3 Evaluate 與 S3 Files 限制判斷。 |
| Skill 4｜驗證 | 部署驗證、權限驗證、錯誤排查 | 33 | 完成本機 canary 故障矩陣、AWS CLI schema 查證與兩份 CloudFormation template validation。 |
| Skill 5｜報告 | Top 3 報告、HTML/文件輸出、週誌 | 30 | 整理 final proposal/demo 素材、AWS/S3 Files 教學書與今日正式日誌。 |

## 每日分數

| 日期 | 掃描 | 比較 | 評估 | 驗證 | 報告 | 每日總分 |
|---|---:|---:|---:|---:|---:|---:|
| 2026-07-13 | 4 | 4 | 4 | 4 | 5 | 21 |
| 2026-07-14 | 2 | 3 | 4 | 3 | 2 | 14 |
| 2026-07-15 | 2 | 2 | 2 | 3 | 5 | 14 |
| 2026-07-16 | 3 | 3 | 5 | 7 | 5 | 23 |
| 2026-07-17 | 4 | 5 | 8 | 9 | 7 | 33 |
| 2026-07-20 | 6 | 4 | 6 | 7 | 6 | 29 |

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
