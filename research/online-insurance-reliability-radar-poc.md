# 線上投保穩定性雷達 PoC 設計

## 定位

這次 PoC 不是直接改公司保單系統，也不是假裝知道內部架構；它是把既有雲端技術雷達套到「線上投保系統穩定性」這個公司場景。

核心問題：

> 在只能從外部觀察、不能取得完整保單系統架構的限制下，能不能用雲端技術雷達找出適合線上投保的穩定性方案，完成比較、報價、測試與報告？

## 雷達流程對應

| 階段 | 在線上投保穩定性 PoC 中做什麼 | 產出 |
|---|---|---|
| S1 Scan | 搜尋非 Bedrock 的穩定性、監控、故障偵測與韌性測試技術 | 候選技術清單 |
| S2 Compare | 依線上投保情境比較適用性：是否低侵入、是否需內部權限、是否碰 PII、是否能黑箱驗證、是否能產出證據 | 比較表與 Top 候選 |
| S2b Quote | 估算候選方案的基本使用成本，例如 canary 執行頻率、CloudWatch alarms、RUM 事件量、FIS action-minute | 成本／使用報價單 |
| S3 Evaluate | 依企業情境評分：導入難度、風險、監控涵蓋率、事件定位能力、可交接性 | 評估分數與採用建議 |
| S4 Validate | 用 mock 投保流程做一次可控驗證：正常、API 500、timeout、前端 JS error | 測試結果與 incident packet |
| S5 Report | 產出主管可讀報告：推薦技術、比較理由、報價、PoC 證據、限制與下一步 | HTML / Markdown 報告 |

## 候選技術方向

先排除 Bedrock / Bedrock AgentCore。優先掃描這些非 Bedrock 類型：

- CloudWatch Synthetics：外部黑箱 canary，模擬投保流程。
- CloudWatch RUM：真實使用者體驗與前端錯誤監測。
- CloudWatch Application Signals：服務健康、latency、availability、faults、errors、SLO 與拓樸。
- AWS Resilience Hub：定義、驗證、追蹤應用韌性與韌性分數。
- AWS Fault Injection Service：受控故障注入，驗證系統能不能承受 timeout、延遲或服務失敗。
- EventBridge + Lambda / Systems Manager Automation：告警後自動整理 incident packet 或執行 runbook。

## 這次可驗證的最小 PoC

因為實習生通常拿不到完整保單系統架構，PoC 採「外部黑箱」方式：

1. 建立一個 mock 線上投保流程。
2. 用 canary 腳本模擬使用者流程。
3. 故意注入三種異常：
   - 報價 API 500
   - 付款前確認 timeout
   - 前端 JS error
4. 自動產生 incident packet：
   - 失敗步驟
   - 截圖
   - console error
   - network evidence
   - 初步分類
   - 建議處理方式
5. 用雷達 S5 產出報告，證明這個方案是否適合線上投保場景。

## 成功標準

- 雷達能從候選技術中選出最適合線上投保穩定性的方案。
- 報價單能估算基本運行成本，並明確標示估算假設。
- PoC 不依賴真實保單系統、不碰客戶資料、不執行付款或出單。
- 模擬異常時，系統能判斷是哪一步故障，並產生可交接的 incident packet。
- 最終報告能清楚說明：推薦什麼、為什麼推薦、成本多少、驗證結果如何、限制是什麼。

## 官方參考來源

- AWS Well-Architected Reliability Pillar：<https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html>
- CloudWatch Synthetics：<https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries.html>
- CloudWatch Application Signals：<https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Monitoring-Sections.html>
- CloudWatch RUM：<https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-RUM.html>
- AWS Resilience Hub score：<https://aws.amazon.com/blogs/mt/how-to-use-the-aws-resilience-hub-score/>
- AWS Fault Injection Service：<https://aws.amazon.com/fis/>
