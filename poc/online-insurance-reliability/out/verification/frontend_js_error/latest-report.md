# 線上投保穩定性 Canary 報告

- Run ID：`2026-07-20T06:21:35.945Z`
- 情境：`frontend_js_error`
- 狀態：`FAIL`
- Base URL：`http://127.0.0.1:62732`
- Timeout：`1500 ms`

## 步驟結果

| Step | OK | HTTP | Duration ms |
|---|---:|---:|---:|
| `homepage_load` | True | 200 | 1.03 |
| `quote_api` | True | 200 | 0.94 |
| `application_preview` | True | 200 | 10.7 |
| `frontend_error_check` | True | 200 | 1.25 |

## Incident Packet

- Failed step：`frontend_error_check`
- Failure category：`frontend_runtime_error`
- Likely owner：`web_frontend`
- Recommended action：保留 console error、release version 與頁面路徑；回查前端 bundle 或資料契約變更。

## 驗證限制

- 此結果來自本機 mock PoC，不代表公司真實系統狀態。
- 測試資料為假資料，不付款、不出單、不使用客戶個資。
