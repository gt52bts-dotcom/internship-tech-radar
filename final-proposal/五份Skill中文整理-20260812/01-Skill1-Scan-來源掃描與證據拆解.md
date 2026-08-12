---
name: scan-cloud-technologies
description: 掃描可信公開 AWS 與開源來源，清理無關內容，產出可追溯的 Skill 1 候選技術 artifact。適用於單一 AWS/GitHub/GitLab/Codeberg URL 匯入、AWS 技術地景探索、GA 證據篩選、來源清理，以及進入候選比較前的清單建立。
---

# Skill 1 Scan：來源掃描與證據拆解

Skill 1 的任務是把可信公開來源轉成可追溯的 `s1.json`。它不排名候選、不評估商業適配性，也不啟動 PoC。

## 核心定位

Skill 1 不是單純摘要新聞，也不是爬蟲。它的價值是先把一篇新聞或一批來源拆成兩層：

- **可採信證據**：原文真的說了什麼，例如支援的服務、功能、可用性、設定方式、限制或官方連結。
- **待驗證推論**：AI 根據原文推導出的可能架構、可能 PoC 形狀、應用情境或後續問題。

後續 Skill 2、Skill 3、Skill 4 都依賴這條界線，避免把官方宣傳、AI 推論和可驗證事實混在一起。

## 執行目錄慣例

同一次評估的所有 artifact 要放在同一個專用資料夾，例如 `./out/run/`。Skill 1 會建立不可變的 `run_id`，後續階段必須保留同一個 `run_id`，並把輸出放在同一個資料夾。不要把不同 run 的 artifact 混在一起。

## 執行方式

從 `radar-redesign/` 執行，並重用 `agentic_cloud_radar/s1.py` 的核心邏輯，不要在 Skill 內複製掃描邏輯。

單一公開 URL：

```powershell
python -m agentic_cloud_radar.cli s1-url `
  --url "<trusted-public-url>" `
  --output .\out\run\s1.json
```

多來源探索：

```powershell
python -m agentic_cloud_radar.cli s1 `
  --input .\samples\landscape-ga-singapore-request.json `
  --output .\out\run\s1.json
```

## 工作流程

1. 如果使用者提供單一公開候選 URL，使用 `s1-url`；如果是技術地景或主題式搜尋，使用 `s1`。
2. 只接受核心程式支援的可信公開 HTTPS 來源。
3. 保留來源 URL、抓取狀態、時間戳、成熟度證據、偵測到的 AWS 服務，以及資料缺口。
4. 可以清理行銷或無關文字，但清理後的候選與證據仍必須可追溯。
5. 缺少 GA、Region、pricing 或服務證據時，標成資料缺口；不要自行推論預覽狀態、可用性或成本。
6. 回報 S1 artifact 路徑，並用繁中摘要候選數量、排除內容、抓取失敗與證據缺口。

## 停止條件

- 輸入無效時，在發出外部請求前停止。
- 不要把 GitHub metadata 當成 AWS GA 證據。
- RSS 只暴露近期項目時，不要宣稱已掃完整年度 archive。
- 不要只因為缺少官方 Region 聲明就丟掉候選；應保留為 Skill 2 與部署 gate 的 review gap。
- 除非使用者明確改變專案限制，否則排除 Bedrock 推薦類候選。

## Explanation 解釋層

除了 evidence layer，每個候選還會有一個 `explanation` 區塊，由 `agentic_cloud_radar/s1_explanation.py` 產生。它是 deterministic rule-based，因此同一頁會產生同樣結構，reviewer 可以回放每一行。

主要欄位：

- `key_points`：原文真的出現的重點句，每一項都有 `evidence_span`。
- `significance`：從原文壓縮出的 before / after / difference。
- `implementation_architecture`：可能元件、資料流與最小 PoC 形狀。
- `possible_application_contexts`：使用者需求卡，加上原文描述的可能應用場景。

每一項都會帶 `derivation` 標記：

- `source_verbatim`：原文逐字或近似逐字證據，可支撐 verified fact。
- `derived_summary`：由原文整理出的摘要，可支撐 verified fact，但仍要保留來源界線。
- `inferred_architecture`：AI 推論的架構，只能作為草案。
- `hypothesis`：假設或可能場景，不能當成已驗證事實。

注意：

- 只有 `source_verbatim` 和 `derived_summary` 可以支撐後續 verified fact。
- `inferred_architecture` 和 `hypothesis` 必須保留在推論區，不得偽裝成官方證據。
- 原文沒提到的元件要保留 `stated_in_source: false`。例如 IAM、CloudWatch 常被記成這樣，因為它們是 reviewer 需要追問、Skill 4 recipe 需要補齊的內容。
- 架構草圖只是人類 review 用的 draft；沒有 registered recipe 時，不能直接拿去部署。

## 驗證

```powershell
python -m unittest tests.test_s1 -v
```

## 階段收尾清單

結束 Skill 1 前，必須完成並回報：

- 更新 `AI_PM_INBOX.md` 或正式 daily log，記錄階段成果、證據、blocker 與下一步。
- 若本次改變專案狀態或跨電腦交接內容，更新 `README.md`、`MIGRATION_STATUS.md` 或其他 handoff 文件。
- 執行相關驗證指令，若無法執行要說明原因。
- 檢查 `git status --short`，並說明變更是否符合預期。
- 在需要共享時提交有意義的 commit。
- 需要同步時 push branch。
- 宣稱已同步前，確認 GitHub 上看得到 pushed state。
- 用清楚繁中留下下一個人類或 AI 需要做的動作。

## 下一階段

把產生的 `s1.json` 交給 `$compare-cloud-candidates`。
