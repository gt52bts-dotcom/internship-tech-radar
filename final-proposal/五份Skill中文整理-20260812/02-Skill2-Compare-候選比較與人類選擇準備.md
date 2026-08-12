---
name: compare-cloud-candidates
description: 將可追溯的 Skill 1 artifact 轉成 evidence-based proposal cards 與比較矩陣，但不自動選出贏家。適用於比較雲端候選技術、檢查官方文件、Region 或 pricing 證據、揭露資料缺口，以及準備 Skill 3 前的人類選擇。
---

# Skill 2 Compare：候選比較與人類選擇準備

Skill 2 只比較 Skill 1 記錄下來的候選。它的任務是幫人類做選擇準備，不自動選候選，也不啟動 Skill 3 評估或 PoC。

## 核心定位

Skill 2 的價值是把「多個候選技術」放到同一張比較桌上。它不是重做 Skill 1，也不是提早做 Skill 3。

- Skill 1：拆來源，分清楚原文證據與 AI 推論。
- Skill 2：用同一組欄位比較多個候選，讓人看得出哪個比較值得進一步評估。
- Skill 3：針對人類選定的一個候選正式評分、估成本、決定是否值得進 PoC。

如果使用者只丟單一新聞 URL 並明確指定就評估這一篇，Skill 2 可以被壓縮成「單一候選整理卡」或前處理轉接層，不應硬演一場比較。

## 執行方式

從 `radar-redesign/` 執行：

```powershell
python -m agentic_cloud_radar.cli s2 `
  --input .\out\run\s1.json `
  --output .\out\run\s2.json
```

重用 `agentic_cloud_radar/s2.py`。不要自行發明官方 URL、pricing、工作負載需求或實作宣稱。

## 工作流程

1. 確認輸入是 S1 artifact，並保留同一個 `run_id`。
2. 重新抓取候選來源，並檢查候選相關的官方連結。
3. 為每個候選建立 proposal card，內容包含 capability、delivery form、maturity、expected benefits、trade-offs、prerequisites、stop conditions 與 evidence gaps。
4. 建立固定比較矩陣，讓所有候選使用同一組比較維度。
5. 只有候選專屬官方證據支持時，才標記新加坡或目標 Region 可用；否則使用 `region_unknown`。
6. pricing page 只能作為待 review 的證據；除非 artifact 中有可用金額，否則不要把它當 PoC 成本估算。
7. 輸出狀態為 `ready_for_human_shortlist`，把所有候選交給 Skill 3。Skill 2 不負責最終選擇；目前流程是在 Skill 3 後的 merged gate 同時呈現 value 和 estimated cost，讓人類一次決定選哪個候選、是否核准 PoC。

## Evidence 規則

- 搜尋結果只能用來發現 URL；引用前必須抓取並驗證該頁內容。
- 來源沒有量化證據時，改善敘述只能保留為 hypothesis。
- 沒有人類輸入時，不要選 champion。
- Region 與 pricing 缺口應保留為 review notes，不要變成額外表單。

## 單一新聞模式

如果只有一個候選，Skill 2 的輸出應該保持精簡：

- 整理 Skill 1 的候選成 Skill 3 可讀格式。
- 補齊 Region、pricing、可驗證性、風險與 stop condition 線索。
- 不排名、不製造 shortlist 戲碼、不宣稱比較結果。

## 驗證

```powershell
python -m unittest tests.test_s2 -v
```

## 階段收尾清單

結束 Skill 2 前，必須完成並回報：

- 更新 `AI_PM_INBOX.md` 或正式 daily log，記錄階段成果、證據、blocker 與下一步。
- 若本次改變專案狀態或跨電腦交接內容，更新 `README.md`、`MIGRATION_STATUS.md` 或其他 handoff 文件。
- 執行相關驗證指令，若無法執行要說明原因。
- 檢查 `git status --short`，並說明變更是否符合預期。
- 在需要共享時提交有意義的 commit。
- 需要同步時 push branch。
- 宣稱已同步前，確認 GitHub 上看得到 pushed state。
- 用清楚繁中留下下一個人類或 AI 需要做的動作。

## 下一階段

把 `s2.json` 和人類選定的一個候選交給 `$evaluate-cloud-candidate`。
