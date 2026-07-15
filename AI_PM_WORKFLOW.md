# AI PM 工作方式

這個專案使用 Codex＋Git 作為輕量 AI PM。目的不是取代正式專案管理系統，而是讓專案在不同電腦與不同工作階段之間仍能延續。

## 每次開始工作

1. 讀取 `AGENTS.md`。
2. 讀取 `PROJECT_MEMORY.md`。
3. 讀取最新的 `work-log-YYYY-MM-DD.md`。
4. 檢查 Git branch、未提交變更與目前阻塞。

## 工作進行中

- 記錄重要決策、驗證結果、阻塞與下一步。
- 週一至週五 17:20 前，只把當日證據暫存在 `AI_PM_INBOX.md`，不提前產生正式日誌。
- 技術細節保留在程式、文件或每日工作日誌，不把所有細節塞進長期記憶。
- 不把密碼、Token、AWS credentials、API key 或個人敏感資料寫入專案。

## 完成一個工作階段

1. 平日 17:20 由自動排程讀取 `AI_PM_INBOX.md`、Git 紀錄與驗證證據，用簡單、合併過的語句產生當日日誌。
2. 若有長期決策或專案狀態改變，再更新 `PROJECT_MEMORY.md`。
3. 執行必要驗證並保留結果。
4. 檢查敏感資訊與 `git diff`。
5. 在有意義的里程碑 commit，並確認 push 成功。

## 日誌分層

- 每日日誌固定使用 `templates/每日實習日誌模板.md`，章節順序與 Notion 的「每日實習日誌模板」相同。
- 每日日誌：保留成果、驗證、問題、決策與下一步。
- 雙週誌：從每日紀錄中整理成果與影響、問題與解法、學習成長及下期重點，不逐日抄寫。
- Final proposal：持續累積專案框架、執行軌跡、成效、成功案例、限制及公司協助成長的證據。

## 五個 Skill 與積分

- 五個 Skill 是五個獨立專案，不是同一條 pipeline 的 S1–S5。
- 🔵 Tech Intel Scan：技術雷達掃描與 Top 3 報告。
- 🟢 Case Study Registry：企業案例庫。
- 🟠 Pick Experiment Tracker：AI vs 人類判斷實驗。
- 🟣 AWS Architecture Scout：AWS 架構檢查與落地補強。
- 🔴 Work Log：AI PM 日誌、跨電腦延續與成果追蹤。
- 積分只使用整數，依完成度細分：準備或釐清 `+1～2`、完成小成果 `+3～4`、完成可用交付 `+5～7`、完成且有驗證的里程碑 `+8～10`。單一成果最高 10 分，避免灌分。
- 每項工作標示與原始目標的關係：`直接扣回目標`、`間接支援`、`偏離目標`。偏離目標的工作仍可記錄，但不灌入 Skill 積分。
- 每日正式日誌同步更新 `SKILL_PROGRESS.md`、README、Notion 日誌、Notion 積分資料庫與 Notion 互動式儀表板。

## Notion 同步目標

- 日誌資料庫：`collection://cd79d9fb-a316-8208-9d99-073d0ac114e1`。
- Skill 積分資料庫：`collection://ed56335a-cd24-4b70-8bf1-6fa25f87d1f0`。
- 儀表板頁：`https://app.notion.com/p/39e9d9fba316813c8e68fa80f8f33d08`。
- 互動式儀表板來源：`dashboard/skill-score-data.json` 與 `dashboard/notion-skill-dashboard.html`。

## Git 是主要延續機制

- 公司環境不依賴 Notion 作為專案記憶。
- 另一台電腦 clone repository 後，Codex 依 `AGENTS.md` 自動讀取專案記憶與最新日誌。
- ZIP、建置輸出、依賴、環境變數與金鑰檔案不進 Git；應同步可重建的原始碼、文件與必要成果。

## Notion 模板來源

- Notion 資料庫：`Cleo的暑期實習日誌(2026CIP)`
- 資料庫網址：`https://app.notion.com/p/de09d9fba31682c0bc34011ff6a2b176`
- 預設模板頁：`https://app.notion.com/p/5bc9d9fba3168391a35e01aba17f1979`
- Git 內文副本：`templates/每日實習日誌模板.md`
- Git 欄位副本：`templates/Cleo的暑期實習日誌(2026CIP)-欄位規則.md`
- 即使另一台電腦或公司環境無法使用 Notion，AI PM 仍依 Git 副本產生日誌。
