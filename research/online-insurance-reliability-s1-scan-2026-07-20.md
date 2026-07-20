# 線上投保穩定性 S1 掃描 - 2026-07-20

## 掃描目標

針對「線上投保系統穩定性」問題，尋找非 Bedrock 的 AWS Blog、AWS 官方文件與 GitHub 案例，判斷是否有人做過類似的外部監測、異常定位、韌性驗證或故障證據產出架構，並整理可借鏡做法。

## 初步結論

最值得借鏡的是 **CloudWatch Synthetics / Playwright canary + incident evidence** 這條路線。

它符合目前限制：

- 可從使用者視角做外部黑箱測試。
- 不需要知道完整保單系統內部架構。
- 不必碰客戶資料、不需要真的付款或出單。
- 可記錄每一步成功／失敗、延遲、截圖、network evidence。
- 可以產生可交接的 incident packet，支援後續 S5 報告。

Application Signals、Resilience Hub、FIS 也值得列入比較，但更偏向「有內部服務或 AWS 架構權限後」的第二階段。

## 候選案例與借鏡點

| 案例 | 類型 | 做法 | 值得借鏡 | 限制 |
|---|---|---|---|---|
| CloudWatch Synthetics canaries | AWS 官方文件 | 用排程 canary 監控 endpoints / APIs，模擬客戶路徑，檢查 availability、latency、截圖與網站內容 | 可作為線上投保 external canary 的核心技術候選 | 若接正式公司系統，需小心測試資料與頻率 |
| CloudWatch Synthetics Playwright runtime | AWS 官方文件 | 用 Playwright 寫瀏覽器流程；每次 canary run 會寫 CloudWatch Logs，且可用 JSON 格式查詢 | 適合投保 journey：首頁、商品頁、試算、付款前確認等多步驟 | 需設計不觸發真實付款／出單的測試路線 |
| API Gateway endpoint monitoring with Synthetics | AWS Blog | 針對 API Gateway endpoint 建 canary，可從 API 或 Swagger template 產生監控步驟 | 若投保報價 API 是 API Gateway 類型，可快速套用 API-level 監控 | 只監 API，不足以看前端白畫面或使用者卡關 |
| Multi-step API monitoring with Synthetics | AWS Blog | 用多個 HTTP endpoint step 監控一段 workflow，並提供 per-step request/response、DNS、TCP、TTFB 等細節 | 非常適合報價、送件、付款前確認等 API sequence | 偏 API workflow；前端互動仍需 Playwright |
| amazon-cloudwatch-synthetics-page-performance | AWS Samples GitHub | CDK 建 canary、custom metric、alarm、SNS email；監控 page load time | 可借 CDK / alarm / custom metric 的寫法，做「投保頁 p95 載入時間」 | 範例很小，只做頁面載入，不含多步驟 journey |
| CloudWatch Application Signals Python demo | AWS Blog + GitHub | Demo 有 `insurances` 與 `billing` 類服務，透過 ADOT / Application Signals 看 service health、latency、traces | 可作為「若有內部微服務權限」時的第二階段架構借鏡 | 需要部署／儀表化服務，不適合實習生黑箱第一版 |
| AWS Resilience Hub + FIS | AWS Blog | Resilience Hub 產生 alarms、SOP、FIS 實驗建議；FIS 測量故障恢復時間 | 適合未來把 PoC 從「偵測」推進到「韌性驗證」 | 通常需要 AWS workload 架構與權限，不適合作為第一天黑箱 PoC |
| aws-samples/fis-template-library | AWS Samples GitHub | 提供 EC2、Aurora、SQS 等 FIS fault injection templates | 可借用「故障情境模板庫」概念，建立我們自己的 mock 投保故障模板 | 真實 FIS 需要內部 AWS 資源與權限 |
| workadventure/playwright-synthetic-monitoring | GitHub | Docker image 定期跑 Playwright tests，提供 `/metrics`、`/healthcheck`、`/last-error` | 很適合本機 PoC：小、可黑箱、可保留最後一次錯誤證據 | 非 AWS 原生；正式公司導入需再接 CloudWatch / Prometheus |
| Basecamp upright | GitHub | Playwright synthetic monitoring engine + Prometheus metrics | 值得借「synthetic monitor + metrics」的產品化概念 | Rails 架構較重，不適合直接拿來做本專案 PoC |

## 建議借鏡組合

### 第一階段：實習生可做的低侵入 PoC

借鏡 `workadventure/playwright-synthetic-monitoring` 與 CloudWatch Synthetics Playwright 的模式：

- 建 mock 線上投保頁。
- 用 Playwright 跑 critical journey。
- 每 5 分鐘或手動跑一次。
- 產出 status、duration、failed step、screenshot、console error、network evidence。
- 失敗時保留 last-error page 或 incident packet。

### 第二階段：雷達推薦的 AWS 化方案

借鏡 CloudWatch Synthetics multi-step API / Playwright runtime：

- 將投保流程拆成 journey-level canary 與 API-level canary。
- journey canary 看使用者視角。
- API canary 看報價、送件、付款前確認等 endpoint。
- CloudWatch Alarm + SNS / ChatOps 做告警。
- S3 / CloudWatch Logs 保存證據。

### 第三階段：若公司願意提供內部架構或測試環境

借鏡 Application Signals、Resilience Hub、FIS：

- Application Signals：看服務拓樸、latency、faults、traces。
- Resilience Hub：整理 resilience policy、alarm、SOP。
- FIS：在測試環境做可控故障注入，驗證 runbook 與恢復時間。

## 對本專案的 S2 比較建議

後續 S2 不應只比「技術酷不酷」，應比：

- 是否可外部黑箱驗證。
- 是否不碰 PII。
- 是否不需要完整內部架構。
- 是否能產生故障證據包。
- 是否可估算成本。
- 是否可從 mock PoC 延伸到 AWS 正式方案。

已依此比較邏輯整理 S2 文件：`research/online-insurance-reliability-s2-compare-2026-07-20.md`。

## 掃描來源

- CloudWatch Synthetics canaries：<https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries.html>
- CloudWatch Synthetics Playwright runtime：<https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Synthetics_WritingCanary_Nodejs_Playwright.html>
- Monitor API Gateway endpoints with Amazon CloudWatch Synthetics：<https://aws.amazon.com/blogs/mt/monitor-api-gateway-endpoints-with-amazon-cloudwatch-synthetics/>
- Multi-step API monitoring using Amazon CloudWatch Synthetics：<https://aws.amazon.com/blogs/mt/multi-step-api-monitoring-using-amazon-cloudwatch-synthetics/>
- amazon-cloudwatch-synthetics-page-performance：<https://github.com/aws-samples/amazon-cloudwatch-synthetics-page-performance>
- Monitoring Python apps using CloudWatch Application Signals：<https://aws.amazon.com/blogs/mt/monitoring-python-apps-using-amazon-cloudwatch-application-signals/>
- application-signals-demo：<https://github.com/aws-observability/application-signals-demo/>
- Shared Responsibility with AWS Resilience Hub：<https://aws.amazon.com/blogs/mt/shared-responsibility-with-aws-resilience-hub/>
- fis-template-library：<https://github.com/aws-samples/fis-template-library>
- workadventure/playwright-synthetic-monitoring：<https://github.com/workadventure/playwright-synthetic-monitoring>
- basecamp/upright：<https://github.com/basecamp/upright>
