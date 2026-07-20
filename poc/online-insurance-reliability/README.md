# 線上投保穩定性黑箱 PoC

這個 PoC 用來驗證「實習生只能從外部觀察或測試時，是否仍能針對線上投保流程做穩定性監控與 incident evidence 產出」。

它對應雲端技術雷達流程：

| 雷達階段 | 本 PoC 做什麼 |
|---|---|
| S0 Demand Input | 固定需求：線上投保流程需能提早發現斷線、API 異常、timeout、前端錯誤 |
| S1 Scan | 已選定 CloudWatch Synthetics / Playwright canary 類型作為借鏡 |
| S2 Compare | 第一版先採黑箱 synthetic canary，因為低侵入、不碰 PII、不需內部架構 |
| S2b Quote | 本機驗證成本為 0；正式 AWS 化後再估 CloudWatch Synthetics、Alarm、Logs/S3 成本 |
| S3 Evaluate | 評估重點是可觀測使用者路徑、故障分類、證據包完整度 |
| S4 Validate | 本目錄實際跑正常與故障情境 |
| S5 Report | canary 會輸出 Markdown 報告與 JSON incident packet |

## 你今天照這樣跑

先開第一個 PowerShell 視窗，啟動 mock 線上投保服務：

```powershell
cd C:\Users\youhs\Documents\實習專案
python poc\online-insurance-reliability\app\mock_insurance_app.py --port 8088 --scenario normal
```

再開第二個 PowerShell 視窗，跑正常情境 canary：

```powershell
cd C:\Users\youhs\Documents\實習專案
python poc\online-insurance-reliability\canary\run_canary.py --base-url http://127.0.0.1:8088 --scenario-label normal
```

你應該會看到 `status=PASS`，並產出：

- `poc/online-insurance-reliability/out/latest-result.json`
- `poc/online-insurance-reliability/out/latest-report.md`

## 故障情境

把第一個 PowerShell 視窗的 server 停掉，改跑以下任一情境。

### 報價 API 500

```powershell
python poc\online-insurance-reliability\app\mock_insurance_app.py --port 8088 --scenario quote_500
python poc\online-insurance-reliability\canary\run_canary.py --base-url http://127.0.0.1:8088 --scenario-label quote_500
```

### 付款前確認 timeout

```powershell
python poc\online-insurance-reliability\app\mock_insurance_app.py --port 8088 --scenario confirmation_timeout
python poc\online-insurance-reliability\canary\run_canary.py --base-url http://127.0.0.1:8088 --scenario-label confirmation_timeout --timeout-ms 1200
```

### 前端錯誤

```powershell
python poc\online-insurance-reliability\app\mock_insurance_app.py --port 8088 --scenario frontend_js_error
python poc\online-insurance-reliability\canary\run_canary.py --base-url http://127.0.0.1:8088 --scenario-label frontend_js_error
```

故障時 canary 會輸出 `status=FAIL`，並保留 `incident-packet-*.json`。這就是之後 S5 報告可以引用的故障證據。

## 目前限制

- 這是本機 mock PoC，不代表公司真實保單系統已發生同樣故障。
- 不碰客戶個資、不付款、不出單。
- 目前用 Python HTTP/API canary 驗證黑箱監測概念；若後續要更像 CloudWatch Synthetics Playwright runtime，可再升級為 Playwright browser journey。
- 本 PoC 不使用 Bedrock。
