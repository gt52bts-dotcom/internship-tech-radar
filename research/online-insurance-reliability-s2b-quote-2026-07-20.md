# 線上投保穩定性 S2b 報價 - 2026-07-20

## 報價定位

本文件承接 S2 比較結果，估算第一階段推薦組合正式 AWS 化後的基本月費：

1. CloudWatch Synthetics / Playwright journey canary。
2. CloudWatch Synthetics multi-step API canary。
3. CloudWatch Alarm。
4. CloudWatch Logs。
5. S3 artifact / report storage。
6. EventBridge + Lambda incident packet。

這是「估算報價」，不是實際帳單。實際費用需依公司正式 Region、canary 數量、執行頻率、log 量、artifact 保留時間、告警數量與是否進 VPC 重算。

## 定價來源與 CLI 驗證

本次用 `intern` profile 查詢 AWS Price List API，未建立任何 AWS 資源，未輸出或保存帳號 ARN / account id。

查詢日期：2026-07-20

查詢 Region：Pricing API 使用 `us-east-1`，產品價格鎖定 `Asia Pacific (Tokyo)` / `ap-northeast-1`。

### CLI 查到的單價

| 項目 | AWS Price List usagetype | 單價 | effective date |
|---|---|---:|---|
| CloudWatch Synthetics canary run | `APN1-CW:Canary-runs` | US$0.0019 / run | 2026-07-01 |
| CloudWatch standard alarm | `APN1-CW:AlarmMonitorUsage` | US$0.10 / alarm-month | 2026-07-01 |
| CloudWatch Logs ingest | `APN1-DataProcessing-Bytes` | US$0.76 / GB | 2026-07-01 |
| CloudWatch Logs storage | `APN1-TimedStorage-ByteHrs` | US$0.033 / GB-month | 2026-07-01 |
| Lambda request | `APN1-Request` | US$0.0000002 / request | 2026-07-01 |
| Lambda duration tier 1 | `APN1-Lambda-GB-Second` | US$0.0000166667 / GB-second | 2026-07-01 |
| S3 Standard storage first 50 TB | `APN1-TimedStorage-ByteHrs` | US$0.025 / GB-month | 2026-07-01 |

官方頁面依據：

- CloudWatch pricing：<https://aws.amazon.com/cloudwatch/pricing/>
- CloudWatch Synthetics canaries：<https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries.html>
- CloudWatch Logs billing：<https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/LogsBillingDetails.html>

## 成本公式

```text
canary_runs_per_month = canary_count * 30 days * 24 hours * 60 minutes / interval_minutes
canary_cost = canary_runs_per_month * 0.0019
alarm_cost = alarm_count * 0.10
logs_ingest_cost = logs_ingest_gb * 0.76
logs_storage_cost = logs_storage_gb * 0.033
s3_storage_cost = s3_artifact_gb * 0.025
lambda_cost = requests * 0.0000002 + requests * memory_gb * duration_seconds * 0.0000166667
```

## 三種方案估算

| 方案 | 用途 | Canary 設定 | 月 runs | Alarm | Log 假設 | Artifact 假設 | Incident Lambda | 預估月費 |
|---|---|---|---:|---:|---|---|---|---:|
| 低頻驗證版 | 實習 PoC / 主管 demo / 非正式環境 | 1 個 canary，每 15 分鐘 | 2,880 | 2 個 | 0.5 GB ingest + 0.5 GB storage | S3 1 GB | 100 次 / 月 | **US$6.09** |
| 正式起步版 | 小規模正式監測，覆蓋 journey + API | 2 個 canary，每 5 分鐘 | 17,280 | 6 個 | 5 GB ingest + 5 GB storage | S3 2 GB | 300 次 / 月 | **US$37.45** |
| 高頻強化版 | 重要時段或高敏感流程，接近即時偵測 | 3 個 canary，每 1 分鐘 | 129,600 | 9 個 | 20 GB ingest + 20 GB storage | S3 10 GB | 1,000 次 / 月 | **US$263.25** |

## 成本拆解

| 方案 | Canary runs | Alarms | Logs ingest | Logs storage | S3 storage | Lambda incident packet | 合計 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 低頻驗證版 | US$5.47 | US$0.20 | US$0.38 | US$0.02 | US$0.02 | US$0.0004 | US$6.09 |
| 正式起步版 | US$32.83 | US$0.60 | US$3.80 | US$0.16 | US$0.05 | US$0.0013 | US$37.45 |
| 高頻強化版 | US$246.24 | US$0.90 | US$15.20 | US$0.66 | US$0.25 | US$0.0045 | US$263.25 |

## 報價結論

第一階段建議採 **低頻驗證版** 或 **正式起步版**。

- 若目標是展示 PoC 與主管討論：先用低頻驗證版，約 US$6 / 月級距。
- 若目標是正式監控一條投保 journey + 一條 API sequence：用正式起步版，約 US$38 / 月級距。
- 不建議第一版直接採高頻強化版；主要成本會被 canary runs 放大，應只用在尖峰時段或真正高風險流程。

## 成本控制建議

- 先把 canary 頻率設為 5 至 15 分鐘，不要一開始每分鐘跑。
- Journey canary 只跑不付款、不出單、不碰 PII 的 preview / sandbox route。
- API canary 只測必要 endpoint，不把每個後端服務都拆成 canary。
- Incident packet 只在失敗時觸發 Lambda，不要每次成功都產完整報告。
- CloudWatch Logs 設 retention，例如 14 或 30 天；長期 evidence 可壓縮後放 S3。
- 高頻 canary 可用排程，只在尖峰時段或活動期間啟用。

## 進入 S3 Evaluate 的建議

S2b 報價通過後，S3 應評估：

- 是否接受 US$6 至 US$38 / 月級距作為第一階段驗證成本。
- 是否能取得一條不付款、不出單、不碰 PII 的測試 journey。
- 是否能建立最少 2 至 6 個 alarm，並定義通知對象與 runbook。
- 是否需要公司安全或法遵確認 canary 測試資料與執行頻率。
