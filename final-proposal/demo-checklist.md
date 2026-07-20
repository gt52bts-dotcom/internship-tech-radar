# Demo Checklist｜Cathay Tech Intel v3

## Demo 目標

用 5 至 8 分鐘證明：這個專案已能在公司 AWS 帳戶中重建、執行、產出報告，並保留足夠證據讓結果可追溯、可審核、可交接。

## Demo 前檢查

| 項目 | 狀態 | 檢查方式 |
|---|---|---|
| GitHub README 顯示 7/17 | 已完成 | 開啟 repository 首頁，確認 7/17 日誌、105 分與 CloudFormation 狀態 |
| 7/17 正式日誌 | 已完成 | `logs/daily/work-log-2026-07-17.md` |
| CloudFormation template | 已完成 | `radar-company-account-complete/radar/manual-cloudformation/cathay-techintel-v3.yaml` |
| CloudFormation README | 已完成 | `radar-company-account-complete/radar/manual-cloudformation/README.md` |
| AI 執行軌跡 | 已完成 | `ai-execution-trace/daily/2026-07-17.md` |
| Final proposal 7/17 素材 | 已整理 | `final-proposal/7-17成果素材.md` |

## Demo 路線

### 1. 專案首頁

- 開啟 GitHub private repository README。
- 指出目前主線已到 CloudFormation 可重建部署。
- 指出 7/17 日誌與 Skill 累積 105 分。

### 2. 執行軌跡圖

- 用 `final-proposal/簡報架構與執行軌跡.md` 的軌跡圖說明演進。
- 重點講三個轉折：
  - CDK bootstrap / SCP 受阻。
  - 改採 Console 手動部署先驗證流程。
  - 再升級成純 CloudFormation 可重建版本。

### 3. CloudFormation 部署證據

- 展示 `manual-cloudformation/README.md` 與 template。
- 說明 template 內容包含 S3、DynamoDB、Secrets、Lambda role、Layer、7 個 Lambda、Step Functions、CloudWatch log groups 與 disabled Scheduler。
- 強調它避開 CDK bootstrap 依賴，較符合公司帳戶限制。

### 4. Step Functions 成功執行

- 展示日誌中的 execution `company-cfn-001`。
- 口頭列出主要數字：
  - S1 `kept_count=27`
  - S2 `kept_count=6`
  - Quote `decision=approve`
  - `total_usd=0.0892`
  - S3/S4 各處理 6 筆

### 5. 報告與治理 artifacts

- 展示或說明 S5 產出：
  - `report.html`
  - `evidence-ledger.json`
  - `review-packet.json`
  - `decision-layer.json`
  - `feedback-stats.json`
  - `audit-packet.json`
  - `cost-estimate.yaml`
- 強調這些 artifacts 讓報告可以被追溯、被人工審核、被稽核。

### 6. 限制說清楚

- 本次是 fallback/rubric 路徑，實際 LLM token 為 0。
- 不可宣稱已完成正式 Anthropic API 評分。
- 後續要補正式 API key 或 Bedrock 路徑。
- Human review stats 需要累積更多人工紀錄才有趨勢解釋力。

## Demo 時建議打開的檔案

| 順序 | 檔案 |
|---:|---|
| 1 | `README.md` |
| 2 | `logs/daily/work-log-2026-07-17.md` |
| 3 | `final-proposal/簡報架構與執行軌跡.md` |
| 4 | `radar-company-account-complete/radar/manual-cloudformation/README.md` |
| 5 | `final-proposal/7-17成果素材.md` |
| 6 | `ai-execution-trace/daily/2026-07-17.md` |

## 一句話收尾

這個 demo 要傳達的不是「AI 自動選了三個技術」而已，而是：我把技術情報流程做成可重建、可驗證、可審核、可交接的公司帳戶版本，並且清楚標示哪些成果已驗證、哪些仍待公司環境下一步確認。
