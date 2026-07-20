# 線上投保穩定性雷達 PoC 設計

## 定位

這次 PoC 不是直接改公司保單系統，也不是假裝知道內部架構；它是把既有雲端技術雷達套到「線上投保系統穩定性」這個公司場景。

核心問題：

> 在只能從外部觀察、不能取得完整保單系統架構的限制下，能不能用雲端技術雷達找出適合線上投保的穩定性方案，完成比較、報價、測試與報告？

## 雷達流程對應

| 階段 | 在線上投保穩定性 PoC 中做什麼 | 產出 |
|---|---|---|
| S-1 Problem Discovery | 當使用者不知道公司痛點時，先用低侵入方式整理問題候選，例如訪談提問、常見金融系統痛點、非敏感文件與既有專案阻礙 | 問題候選清單 |
| S0 Demand Input | 使用者先輸入應用端需求：目前遇到什麼問題、舊方法為何不夠、限制條件、成功標準與不採用範圍 | 需求卡與掃描邊界 |
| S1 Scan | 搜尋非 Bedrock 的穩定性、監控、故障偵測與韌性測試技術 | 候選技術清單 |
| S2 Compare | 依線上投保情境比較適用性：是否低侵入、是否需內部權限、是否碰 PII、是否能黑箱驗證、是否能產出證據 | 比較表與 Top 候選 |
| S2b Quote | 估算候選方案的基本使用成本，例如 canary 執行頻率、CloudWatch alarms、RUM 事件量、FIS action-minute | 成本／使用報價單 |
| S3 Evaluate | 依企業情境評分：導入難度、風險、監控涵蓋率、事件定位能力、可交接性 | 評估分數與採用建議 |
| S4 Validate | 用 mock 投保流程做一次可控驗證：正常、API 500、timeout、前端 JS error | 測試結果與 incident packet |
| S5 Report | 產出主管可讀報告：推薦技術、比較理由、報價、PoC 證據、限制與下一步 | HTML / Markdown 報告 |

## S0 應用端需求輸入

未來 GUI 的第一步不應該讓使用者直接按「掃描新技術」，而是先填一張需求卡。這能避免 S1 掃出大量跟實際業務痛點無關的技術。

但實習生或跨部門使用者不一定知道公司真正痛點，所以 S0 前面可以有一個 S-1 問題發現層。S-1 不直接決定技術，也不宣稱公司真的有某個故障；它只整理「值得拿去問主管或業務單位確認」的問題候選。

S-1 可用的低侵入來源：

- 主管或 mentor 的一句方向，例如「最近想看穩定性」、「想降低突發事件」。
- 使用者能觀察到的外部流程，例如公開投保頁、客服 FAQ、公告、維護訊息。
- 專案既有阻礙，例如權限限制、部署驗證困難、故障證據不易交接。
- 常見金融系統痛點，例如流程 timeout、尖峰流量、第三方付款依賴、前端錯誤、跨服務定位困難。
- 產業或 AWS 官方可靠性最佳實務，用來反推可討論的問題類型。

S-1 的產出不是正式需求，而是一份候選問題清單，例如：

| 候選問題 | 為什麼值得問 | 是否可由實習生低侵入驗證 |
|---|---|---|
| 線上投保流程是否能提早發現斷線或 timeout | 直接影響投保轉換與客訴 | 可以用 mock journey / black-box canary 驗證 |
| 異常發生後是否能快速整理故障證據 | 工程師需要截圖、時間、失敗步驟、network evidence | 可以用 incident packet PoC 驗證 |
| 舊有監控是否偏後端，較難看到使用者體驗 | 前端白畫面或 JS error 不一定等於後端掛掉 | 可以用 RUM / synthetic concept 驗證 |

人類確認其中一個候選問題後，才進入 S0 需求卡。

以線上投保穩定性為例，S0 需求卡可包含：

- 應用場景：線上投保流程。
- 遇到的問題：斷線、白畫面、報價 API 不穩、付款前流程 timeout、異常發生後難以快速定位。
- 舊有方法限制：只靠人工巡檢或事後 log 排查，可能太晚發現，也不易整理完整故障證據。
- 成功標準：能從使用者視角提早偵測流程異常、分類故障步驟、保留截圖與 network evidence、產出 incident packet。
- 限制條件：不碰客戶 PII、不真的付款或出單、不需要完整內部架構、不使用 Bedrock。
- 掃描範圍：外部黑箱監測、RUM、Application Signals、韌性評估、故障注入、自動 runbook。
- 排除範圍：客服聊天機器人、推薦系統、資料湖、生成式內容、與穩定性無關的新服務。
- 評分權重：低侵入性、線上投保適配度、異常定位能力、成本可控、可交接性、可做 PoC 驗證。

S0 通過後，S1 才開始掃描。S1 之後仍可保留人工候選池檢查，但那只是確認候選沒有偏題，不是重新定義需求。

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

1. 先做 S-1 問題候選蒐集，整理「線上投保穩定性」為可向主管確認的候選痛點。
2. 建立 S0 需求卡，明確指定線上投保穩定性與限制條件。
3. 讓雷達依 S0 掃描並比較候選技術。
4. 產出候選方案報價與採用建議。
5. 建立一個 mock 線上投保流程。
6. 用 canary 腳本模擬使用者流程。
7. 故意注入三種異常：
   - 報價 API 500
   - 付款前確認 timeout
   - 前端 JS error
8. 自動產生 incident packet：
   - 失敗步驟
   - 截圖
   - console error
   - network evidence
   - 初步分類
   - 建議處理方式
9. 用雷達 S5 產出報告，證明這個方案是否適合線上投保場景。

## 成功標準

- 雷達能從候選技術中選出最適合線上投保穩定性的方案。
- S-1 問題候選能清楚標示「待人類確認」，不把推測寫成公司已發生的問題。
- S0 需求卡能清楚約束掃描範圍，避免掃出與線上投保穩定性無關的候選。
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
