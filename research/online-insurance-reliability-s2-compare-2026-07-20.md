# 線上投保穩定性 S2 比較 - 2026-07-20

## 比較目標

本文件承接 `online-insurance-reliability-s1-scan-2026-07-20.md`，把 S1 掃到的候選技術放進線上投保情境比較。

S2 不比較「技術酷不酷」，而是比較它是否能在目前限制下產生可驗證價值：

- 可從外部黑箱驗證。
- 不碰客戶 PII。
- 不需要完整內部架構。
- 能產生故障證據包。
- 可估算成本。
- 可從 mock PoC 延伸到 AWS 正式方案。

## 比較假設

- 使用者目前拿不到完整保單系統架構，只能從外部觀察、模擬或測試。
- 不使用 Bedrock / Bedrock AgentCore 作為推薦實作路線。
- 不對真實客戶付款、不出單、不寫入真實保單資料。
- 第一階段只需要證明「能提早偵測異常、定位失敗步驟、保留 incident evidence」。
- 若需公司內部服務拓樸、AWS workload inventory、agent instrumentation 或故障注入權限，列為第二階段。

## 評分方式

每項 1 至 5 分：

| 分數 | 意義 |
|---:|---|
| 5 | 非常符合，目前即可驗證或直接延伸 |
| 4 | 符合，但需少量設計或權限 |
| 3 | 可用，但限制明顯 |
| 2 | 只適合作為輔助 |
| 1 | 不適合第一階段 |

S2 分數是中間比較，不是最終採用分數。最終 Top 3 應在 S2b Quote、S3 Evaluate、S4 Validate 都完成後再定。

## 候選技術比較表

| 候選技術 | 外部黑箱驗證 | 不碰 PII | 不需完整架構 | 故障證據包 | 可估成本 | 可延伸 AWS 正式方案 | 總分 | S2 判斷 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| CloudWatch Synthetics - Playwright journey canary | 5 | 4 | 5 | 5 | 5 | 5 | 29 | 第一階段主方案 |
| CloudWatch Synthetics - multi-step API canary | 4 | 5 | 4 | 4 | 5 | 5 | 27 | 第一階段 API 輔助方案 |
| workadventure / Playwright synthetic monitoring 類本機方案 | 5 | 5 | 5 | 4 | 5 | 3 | 27 | 本機 PoC 借鏡與驗證方案 |
| EventBridge + Lambda incident packet / runbook | 3 | 5 | 3 | 5 | 4 | 5 | 25 | 告警後證據整理方案 |
| AWS Samples page performance canary | 5 | 5 | 5 | 2 | 5 | 5 | 27 | 頁面載入監控輔助，不足以覆蓋投保 journey |
| CloudWatch RUM | 3 | 3 | 3 | 3 | 4 | 5 | 21 | 第二階段，需處理前端植入與 PII 遮罩 |
| CloudWatch Application Signals | 1 | 4 | 1 | 4 | 4 | 4 | 18 | 第二階段，需內部服務與儀表化權限 |
| AWS Resilience Hub | 1 | 5 | 1 | 3 | 3 | 4 | 17 | 第二階段，用於韌性成熟度與 SOP |
| AWS Fault Injection Service | 1 | 5 | 1 | 3 | 3 | 4 | 17 | 第二階段，需測試環境與故障注入權限 |
| Basecamp upright 類完整 synthetic monitoring engine | 4 | 5 | 4 | 4 | 3 | 2 | 22 | 概念可借鏡，但架構較重，不作第一版 |

## 第一階段推薦組合

### 1. 主監測：CloudWatch Synthetics / Playwright journey canary

推薦理由：

- 最符合「從使用者視角」測線上投保流程。
- 可以覆蓋首頁、商品頁、報價、付款前確認等多步驟 journey。
- 可產生截圖、步驟狀態、錯誤訊息與 CloudWatch Logs。
- 從本機 mock PoC 延伸到 AWS 正式方案最直覺。

目前 PoC 對應：

- `poc/online-insurance-reliability/app/mock_insurance_app.py`
- `poc/online-insurance-reliability/canary/run_canary.py`
- `poc/online-insurance-reliability/out/verification/`

### 2. API 輔助：CloudWatch Synthetics multi-step API canary

推薦理由：

- 線上投保流程通常會有報價、送件、付款前確認等 API sequence。
- API canary 可以更快定位是前端壞、入口壞、還是某個 API step 壞。
- 適合和 Playwright journey canary 配合：journey 看使用者體驗，API canary 看服務序列。

### 3. 事件證據：EventBridge + Lambda incident packet

推薦理由：

- Canary 失敗後，只告警還不夠，還要整理「人類能接手」的證據。
- incident packet 可以保存 failed step、HTTP status、duration、錯誤分類、建議處理方式。
- 這條路線能接回既有技術雷達的 Evidence Ledger、Human Review Gate 與 S5 report。

## 不作為第一階段主方案的原因

| 技術 | 暫不主推原因 | 保留價值 |
|---|---|---|
| CloudWatch RUM | 需要前端植入與資料治理設計，可能碰到真實使用者資料與 PII 遮罩問題 | 第二階段可補真實使用者體驗 |
| Application Signals | 需要內部服務、agent instrumentation 與服務拓樸，不符合小實習生黑箱限制 | 若公司給測試環境，可補 trace、latency、faults |
| Resilience Hub | 需要 AWS workload inventory 與架構資訊 | 後續可做韌性分數、SOP、alarm 建議 |
| FIS | 需要可控測試環境與故障注入權限，不能對真實投保系統亂打 | 後續可驗證 timeout、延遲、服務失敗下的恢復能力 |
| 完整 synthetic monitoring engine | 導入成本高，會把今天 PoC 拉太大 | 可借 `/metrics`、`/healthcheck`、`/last-error` 的產品化設計 |

## S2 結論

第一階段應採：

1. **CloudWatch Synthetics / Playwright journey canary** 作為主方案。
2. **Multi-step API canary** 作為 API-level 輔助。
3. **EventBridge + Lambda incident packet** 作為告警後證據整理與 S5 報告輸出。

本機 PoC 已先用 mock 投保流程與 synthetic canary 驗證這個組合的核心概念：

- `normal` 可通過。
- `quote_500` 可定位到報價 API。
- `confirmation_timeout` 可定位到付款前確認 timeout。
- `frontend_js_error` 可定位到前端錯誤。

下一步進入 S2b Quote：估算若正式 AWS 化，依 canary 頻率、保留報告、CloudWatch alarms、Lambda incident packet 執行次數所需的基本成本。
