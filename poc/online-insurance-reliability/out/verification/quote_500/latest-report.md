# 線上投保穩定性 Canary 報告

- Run ID：`2026-07-20T06:21:33.903Z`
- 情境：`quote_500`
- 狀態：`FAIL`
- Base URL：`http://127.0.0.1:62725`
- Timeout：`1500 ms`

## 步驟結果

| Step | OK | HTTP | Duration ms |
|---|---:|---:|---:|
| `homepage_load` | True | 200 | 13.68 |
| `quote_api` | False | 500 | 13.77 |

## Incident Packet

- Failed step：`quote_api`
- Failure category：`api_5xx_or_quote_engine_failure`
- Likely owner：`quote_service`
- Recommended action：檢查報價服務健康、最近部署與錯誤率；若正式化可接 CloudWatch Alarm 與 runbook。

## 驗證限制

- 此結果來自本機 mock PoC，不代表公司真實系統狀態。
- 測試資料為假資料，不付款、不出單、不使用客戶個資。
