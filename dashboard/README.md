# Cleo 的 Skill 進度互動儀錶板

> 這份 dashboard 是 GitHub private repository 內的可攜式 Skill 進度資料。Notion 版本可嵌入 `cleo-skill-dashboard.html`，Git 版本則作為每日 17:00 AI PM 同步的 source of truth。

## 最新狀態

- 累積總分：91 分
- 最新日期：2026-07-20
- 今日重點：改採硬審核口徑重算所有日期；7/20 只計研究、CLI 查證、本機 PoC 與 template validation，尚未部署 S3 Files，因此降為 14 分。

| Skill | 說明 | 累積分數 | 最新變化 |
|---|---|---:|---|
| Skill 1｜掃描 | 資料來源掃描、候選技術收集 | 14 | 只保留已支撐 pipeline 或 PoC 的掃描成果；一般研究降為低分。 |
| Skill 2｜比較 | 候選技術比較、案例對照 | 14 | 已完成比較邏輯與候選篩選，但非正式驗證的比較不給高分。 |
| Skill 3｜評估 | 評分邏輯、AHP/rubric/LLM 輔助評估 | 19 | 評估治理與 fallback 設計有進展；真實 LLM/API 與 human feedback 仍有限。 |
| Skill 4｜驗證 | 部署驗證、權限驗證、錯誤排查 | 26 | 最高分集中於公司帳戶端到端與 CloudFormation PoC 驗證。 |
| Skill 5｜報告 | Top 3 報告、HTML/文件輸出、週誌 | 18 | 只把核心報告 artifact 算高一點，簡報與日誌支援不拉高核心分數。 |

## 每日分數

| 日期 | 掃描 | 比較 | 評估 | 驗證 | 報告 | 每日總分 |
|---|---:|---:|---:|---:|---:|---:|
| 2026-07-13 | 3 | 3 | 3 | 5 | 3 | 17 |
| 2026-07-14 | 2 | 2 | 2 | 2 | 2 | 10 |
| 2026-07-15 | 1 | 1 | 1 | 2 | 3 | 8 |
| 2026-07-16 | 2 | 2 | 4 | 6 | 4 | 18 |
| 2026-07-17 | 3 | 4 | 6 | 7 | 4 | 24 |
| 2026-07-20 | 3 | 2 | 3 | 4 | 2 | 14 |

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
