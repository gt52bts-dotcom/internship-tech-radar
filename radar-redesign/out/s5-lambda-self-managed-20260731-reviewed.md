# 技術驗證報告｜AWS Lambda 宣布自主管理程式碼儲存空間 - AWS

- 報告狀態：interim
- Run ID：direct-url-20260729-9d2a3d3c
- 來源：https://aws.amazon.com/tw/about-aws/whats-new/2026/07/lambda-self-managed-code-storage/

## 一句結論

> PoC 技術驗證與 AWS Console review 均已確認成功；待執行受控 cleanup。

## 評估摘要

| 指標 | 結果 |
| --- | --- |
| Skill 3 加權分 | 4.0 |
| 信心 | medium |
| 區域狀態 | available_ap_southeast_1 |
| 建議進行 Skill 4 PoC | 是 |
| 成本 | estimated |

## PoC 成本估算報價單

- Quote ID：POC-QUOTE-09FE81935092
- 區域：ap-southeast-1
- 幣別：USD
- 價格快照：2026-07-31
- 有效期限：2026-08-07
- 情境總額：低 **$0.000072**／預期 **$0.000249**／高 **$0.000886**
- 建議核准上限：**$0.05**

### 預期情境明細

| 項目 | 費率 | 用量 | 小計 USD |
| --- | ---: | ---: | ---: |
| AWS Lambda requests | 0.0000002 USD/request | 15 requests | 0.000003 |
| AWS Lambda x86 duration | 0.000016667 USD/GB-second | 5 GB-seconds | 0.000083 |
| S3 Standard 儲存 | 0.025 USD/GB-month | 0.000027397 GB-month | 0.000001 |
| S3 Tier 1 PUT/COPY/POST/LIST | 0.000005 USD/request | 30 requests | 0.00015 |
| S3 Tier 2 GET 與其他請求 | 0.0000004 USD/request | 30 requests | 0.000012 |
| **預期總額** |  |  | **0.000249** |

### 報價假設與限制

- 預期情境假設：1 小時、0.02 GB artifact、15 次 Lambda request、5 GB-seconds。
- Tax, private pricing, Savings Plans, credits and Free Tier are excluded.
- Unexpected data transfer, retries, CloudWatch log ingestion, and resources outside the registered recipe are excluded.
- Recheck the Lambda and S3 pricing pages before deployment if the quote has expired.
- 這是依 AWS 公開牌價與明列用量假設產生的非約束性 PoC 成本估算，不是 AWS 帳單、發票或正式銷售報價。實際費用以部署後的 AWS 帳務資料為準。

### 官方價格來源

- [AWS Lambda public request price](https://aws.amazon.com/lambda/pricing/)
- [AWS Price List API snapshot, Asia Pacific (Singapore), first 50 TB](https://aws.amazon.com/s3/pricing/)
- [AWS Price List API interpretation](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/finding-prices-in-service-price-list-files.html)
- [EC2 On-Demand pricing terms](https://aws.amazon.com/ec2/pricing/on-demand/)

## 預估成本 vs 可歸因實際帳務成本

| 項目 | 狀態 | 金額 USD | 證據 |
| --- | --- | ---: | --- |
| Skill 3 公開牌價估算 | estimated | 0.000249 | POC-QUOTE-09FE81935092 |
| 可歸因實際帳務成本 | pending | unknown | not_available |
| 差異（實際 - 預估） | pending_actual_cost | unknown | Actual cost is shown only when an attributable AWS Billing, Cost Explorer, or CUR artifact records it; runtime duration is not converted into actual cost. |

- 實際成本狀態：pending。No attributable AWS Billing, Cost Explorer, or CUR artifact was provided.
- 不以 EC2 執行時間、CloudFormation 狀態或 runtime artifact 推算實際 AWS 帳務成本。

## 技術驗證

| 檢查 | 狀態 |
| --- | --- |
| Skill 4 validation | poc_ready_for_manual_start |
| CloudFormation | CREATE_COMPLETE |
| 自動化驗證 | verified |
| AWS Console review | confirmed |
| cleanup | ready_for_manual_cleanup |

## 已證實的事實

- 官方來源已記錄：https://aws.amazon.com/tw/about-aws/whats-new/2026/07/lambda-self-managed-code-storage/
- Skill 3 加權分已依固定 rubric 計算：4.0
- PoC 成本估算報價單已建立：POC-QUOTE-09FE81935092，預期 USD 0.000249。
- CloudFormation stack 已達 CREATE_COMPLETE。
- Skill 4 自動化驗證已通過：cloudformation_reference_mode。
- Skill 4 自動化驗證已通過：lambda_invoke。

## 尚未驗證或證據不足

- No candidate-relevant official AWS pricing page was fetched in this S2 run.
- No candidate-relevant official AWS Region or availability page was fetched in this S2 run.
- 可歸因實際帳務成本尚未由 Cost Explorer、Billing 或 CUR artifact 證實；不得以 runtime 估算代替。
- cleanup 尚未完成或尚未記錄。

## 後續提醒

- No safe non-production environment or required permission is available.
- Official pricing or cleanup cannot be bounded within the USD 3 cap.
- No measurable baseline exists for the proposed workflow.

## 證據帳本

| 敘述 | 類型 | 狀態 | 證據 |
| --- | --- | --- | --- |
| 候選技術的公開來源 | source-backed fact | recorded | https://aws.amazon.com/tw/about-aws/whats-new/2026/07/lambda-self-managed-code-storage/ |
| recipe | runtime evidence | lambda_self_managed_s3_code_storage_cdk | S4 runtime artifact |
| cloudformation_reference_mode | runtime evidence | verified | S4 runtime artifact |
| lambda_invoke | runtime evidence | verified | S4 runtime artifact |
| PoC 成本估算 | public list-price estimate | estimated | POC-QUOTE-09FE81935092 |
| PoC 可歸因實際帳務成本 | AWS billing evidence | pending | No attributable AWS Billing, Cost Explorer, or CUR artifact was provided. |
