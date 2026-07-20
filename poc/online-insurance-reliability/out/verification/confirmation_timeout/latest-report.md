# 線上投保穩定性 Canary 報告

- Run ID：`2026-07-20T06:21:34.424Z`
- 情境：`confirmation_timeout`
- 狀態：`FAIL`
- Base URL：`http://127.0.0.1:62728`
- Timeout：`1200 ms`

## 步驟結果

| Step | OK | HTTP | Duration ms |
|---|---:|---:|---:|
| `homepage_load` | True | 200 | 1.35 |
| `quote_api` | True | 200 | 12.08 |

## Incident Packet

- Failed step：`application_preview`
- Failure category：`timeout`
- Likely owner：`application_or_downstream_dependency`
- Recommended action：先檢查付款前確認或下游服務延遲，保留該 step 的 request timestamp 與 timeout threshold。

## 驗證限制

- 此結果來自本機 mock PoC，不代表公司真實系統狀態。
- 測試資料為假資料，不付款、不出單、不使用客戶個資。
