# AI PM 工作方式

這個專案使用 Codex＋Git 作為輕量 AI PM。目的不是取代正式專案管理系統，而是讓專案在不同電腦與不同工作階段之間仍能延續。

## 每次開始工作

1. 讀取 `AGENTS.md`。
2. 讀取 `PROJECT_MEMORY.md`。
3. 讀取最新的 `logs/daily/work-log-YYYY-MM-DD.md`。
4. 檢查 Git branch、未提交變更與目前阻塞。

## 工作進行中

- 記錄重要決策、驗證結果、阻塞與下一步。
- 週一至週五 17:00 前，只把當日證據暫存在 `AI_PM_INBOX.md`，不提前產生正式日誌；正式日誌放在 `logs/daily/`。
- 技術細節保留在程式、文件或每日工作日誌，不把所有細節塞進長期記憶。
- 不把密碼、Token、AWS credentials、API key 或個人敏感資料寫入專案。
- 開始一項實作或交付前，先定義 checkpoint：目標、對應 Skill 或動作、完成條件、驗證方式與預期證據。
- 每完成一個 checkpoint，都要留下可檢查證據，例如 Console 截圖、檔案 diff、命令輸出、測試結果、資源 ARN、Notion/Git 更新紀錄或明確的使用者回報。
- 若 checkpoint、驗證方式、時間軸或主管期待不清楚，AI PM 應主動反問；不能用模糊進度灌分。
- 自 2026-07-17 起，每天同步維護 AI 自己的執行軌跡 Markdown，檔案放在 `ai-execution-trace/daily/YYYY-MM-DD.md`。此檔每小時追加一次，用 outcome-based 方式記錄使用者指令／更正、AI PM 判斷、實際動作、驗證證據與待接續事項；不寫專案前情提要，不取代正式工作日誌。

## 完成一個工作階段

1. 平日 17:00 由自動排程讀取 `AI_PM_INBOX.md`、Git 紀錄與驗證證據，以 Cleo 本人的白話簡潔口吻，用短句與合併過的語句產生當日日誌。
2. 若有長期決策或專案狀態改變，再更新 `PROJECT_MEMORY.md`。
3. 執行必要驗證並保留結果。
4. 檢查敏感資訊與 `git diff`。
5. 在有意義的里程碑 commit，並確認 push 成功。

## 日誌分層

- 每日日誌固定使用 `templates/每日實習日誌模板.md`，章節順序與 Notion 的「每日實習日誌模板」相同。
- 每日日誌：由 Codex 代表 Cleo 書寫，語氣要像 Cleo 本人的實習紀錄：白話、少廢話、短句、直接。第一段先讓人看懂今天在做什麼，以及這件事對專案的幫助。可以用「我」，但不要每句都硬塞主詞；重點放在實際工作、成果、驗證、問題、決策與下一步。驗證段要寫成「怎麼確認有做出來」，不要堆長指令、檔名或專有名詞。句子自然但不聊天化，主管讀起來要清楚專業；Codex 只能作為協助整理、驗證與追蹤的工具，不當敘事主體。
- AI 執行軌跡：以 AI PM 視角保留使用者指令、使用者更正、AI 判斷、工具動作、產出、驗證證據與待接續事項，用來補足「為什麼這樣推進」的脈絡。
- 雙週誌：從每日紀錄中整理成果與影響、問題與解法、學習成長及下期重點，不逐日抄寫。
- Final proposal：持續累積專案框架、執行軌跡、成效、成功案例、限制及公司協助成長的證據。

## 五個 Skill 與積分

- 五個 Skill 依專案設計分成五個可獨立追蹤的階段。
- 🔵 Skill 1｜掃描 Scan：蒐集來源、清理資料與產生候選清單。
- 🟢 Skill 2｜比較 Compare：依公司需求比較、排序與篩選候選。
- 🟠 Skill 3｜評估 Evaluate：依評分準則與案例證據進行深度評估。
- 🟣 Skill 4｜驗證 Validate：獨立重新評分、檢查分歧與驗證結果。
- 🔴 Skill 5｜報告 Report：選出 Top 3、整理報告與呈現成果。
- 積分只使用整數，五個 Skill 的每日加總最高 10 分，避免把同一天的多個文件或同一成果重複灌到不同 Skill。研究、文件整理、模板驗證、單點 CLI 查證通常每日 1～3 分；本機 PoC 或離線驗證通常每日 3～5 分；公司帳戶端到端成功但仍有 fallback、未回驗或品質限制時通常每日 6～8 分；9～10 分只保留給可重現、可展示、品質已回驗且對核心目標有明確里程碑意義的成果。
- 每項工作標示與原始目標的關係：`直接扣回目標`、`間接支援`、`偏離目標`。偏離目標的工作仍可記錄，但不灌入 Skill 積分。
- 每日正式日誌同步更新 `SKILL_PROGRESS.md`、GitHub 儀表板、HTML 互動儀表板、README、Notion 日誌中的五個 Skill 積分欄位與 Notion 儀表板；同一項工作可分配到多個 Skill，但五項合計仍不得超過 10 分，每個 Skill 必須有不同且可驗證的成果，避免重複灌分。
- 每日計分前先檢查是否已有事前定義的 checkpoint 與事後驗證；缺少驗證的項目只可記為進度或待驗證，不給高分。

## 主管評分表自評

- 自 2026-07-21 起，每日日誌可補充「主管評分表自評」，追蹤四大項目：組織認同／組織承諾、盡責、團隊合作、創新求變。
- 同步追蹤主管表單的 15 項行為觀察，使用 1 到 5 分；只根據日誌、Git 產出、驗證結果、主管或 mentor 回饋等可檢查證據給分。
- 累計自評保存於 `MENTOR_EVALUATION_PROGRESS.md`；每日只寫當天新增證據，避免日誌變長。
- Notion 入口頁為 `Cleo｜主管評分自評儀表板`：`https://app.notion.com/p/3a49d9fba316816c8f95d2a2ff997350`，並已從 Skill 積分儀表板底部連回。
- 這是實習生自評與補強提醒，不是主管正式成績；若缺少外部回饋，要明確標示「待主管確認」。

## Notion 同步目標

- 日誌資料庫：`collection://cd79d9fb-a316-8208-9d99-073d0ac114e1`。
- Skill 積分資料庫：`collection://ed56335a-cd24-4b70-8bf1-6fa25f87d1f0`。
- 儀表板頁：`https://app.notion.com/p/39e9d9fba316813c8e68fa80f8f33d08`，已移入 `Cleo的暑期實習日誌(2026CIP)` 資料庫，從 `📊 儀表板入口` 檢視開啟。
- 互動式儀表板來源：`dashboard/skill-score-data.json` 與 `dashboard/notion-skill-dashboard.html`。
- GitHub Private 儀表板入口：`dashboard/README.md`；不啟用會公開公司日誌內容的個人 GitHub Pages。

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
