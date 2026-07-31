# 技術驗證報告｜Launching S3 Files, making S3 buckets accessible as file systems | AWS News Blog

- 報告狀態：final
- Run ID：direct-url-20260730-7339a0b8
- 來源：https://aws.amazon.com/tw/blogs/aws/launching-s3-files-making-s3-buckets-accessible-as-file-systems/

## 一句結論

> PoC 技術驗證通過，且 cleanup 已完成。

## 評估摘要

| 指標 | 結果 |
| --- | --- |
| Skill 3 加權分 | 4.4 |
| 信心 | medium |
| 區域狀態 | available_ap_southeast_1 |
| 建議低風險 Skill 4 驗證 | 是 |
| 達到 PoC 審查門檻 | 是 |
| 成本 | estimated |

## PoC 成本估算報價單

- Quote ID：POC-QUOTE-4C820F98175B
- 區域：ap-southeast-1
- 幣別：USD
- 價格快照：2026-07-30
- 有效期限：2026-08-06
- 情境總額：低 **$0.018037**／預期 **$0.04719**／高 **$0.150962**
- 建議核准上限：**$0.20**

### 預期情境明細

| 項目 | 費率 | 用量 | 小計 USD |
| --- | ---: | ---: | ---: |
| EC2 t3.micro Linux 隨需執行個體 | 0.0132 USD/instance-hour | 2 hours | 0.0264 |
| EBS gp3 根磁碟 | 0.096 USD/GB-month | 0.021917808 GB-month | 0.002104 |
| S3 Files 高效能儲存 | 0.36 USD/GB-month | 0.000273973 GB-month | 0.000099 |
| S3 Files write access | 0.06 USD/GB | 0.1 GB | 0.006 |
| S3 Files sync export/read | 0.03 USD/GB | 0.1 GB | 0.003 |
| S3 Files small read | 0.03 USD/GB | 0.1 GB | 0.003 |
| S3 Files sync import/write | 0.06 USD/GB | 0.1 GB | 0.006 |
| S3 Standard 儲存 | 0.025 USD/GB-month | 0.000273973 GB-month | 0.000007 |
| S3 Tier 1 PUT/COPY/POST/LIST | 0.000005 USD/request | 100 requests | 0.0005 |
| S3 Tier 2 GET 與其他請求 | 0.0000004 USD/request | 200 requests | 0.00008 |
| **預期總額** |  |  | **0.04719** |

### 報價假設與限制

- 預期情境使用 2 小時、0.1 GB active storage。
- Tax, private pricing, Savings Plans, credits and Free Tier are excluded.
- Unexpected data transfer, retries, log ingestion and resources outside the registered recipe are excluded.
- S3 Files access rates are public example rates; recheck the AWS pricing page before deployment if the quote has expired.
- 這是依 AWS 公開牌價與明列用量假設產生的非約束性 PoC 成本估算，不是 AWS 帳單、發票或正式銷售報價。實際費用以部署後的 AWS 帳務資料為準。

### 官方價格來源

- [AWS public EC2 price file, Asia Pacific (Singapore)](https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/Asia%20Pacific%20(Singapore)/Linux/index.json)
- [AWS Price List API snapshot, Asia Pacific (Singapore)](https://aws.amazon.com/ebs/pricing/)
- [AWS Price List API snapshot, Asia Pacific (Singapore)](https://aws.amazon.com/s3/pricing/)
- [AWS Price List API interpretation](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/finding-prices-in-service-price-list-files.html)
- [EC2 On-Demand pricing terms](https://aws.amazon.com/ec2/pricing/on-demand/)

## 預估成本 vs 可歸因實際帳務成本

| 項目 | 狀態 | 金額 USD | 證據 |
| --- | --- | ---: | --- |
| Skill 3 公開牌價估算 | estimated | 0.04719 | POC-QUOTE-4C820F98175B |
| 可歸因實際帳務成本 | pending | unknown | not_available |
| 差異（實際 - 預估） | pending_actual_cost | unknown | Actual cost is shown only when an attributable AWS Billing, Cost Explorer, or CUR artifact records it; runtime duration is not converted into actual cost. |

- 實際成本狀態：pending。No attributable AWS Billing, Cost Explorer, or CUR artifact was provided.
- 不以 EC2 執行時間、CloudFormation 狀態或 runtime artifact 推算實際 AWS 帳務成本。

## 技術驗證

| 檢查 | 狀態 |
| --- | --- |
| Skill 4 validation | poc_ready_for_manual_start |
| CloudFormation | CREATE_COMPLETE |
| 自動化驗證 | verified, verified, Success |
| AWS Console review | confirmed |
| cleanup | verified |

## 已證實的事實

- 官方來源已記錄：https://aws.amazon.com/tw/blogs/aws/launching-s3-files-making-s3-buckets-accessible-as-file-systems/
- Skill 3 加權分已依固定 rubric 計算：4.4
- PoC 成本估算報價單已建立：POC-QUOTE-4C820F98175B，預期 USD 0.04719。
- CloudFormation stack 已達 CREATE_COMPLETE。
- Skill 4 自動化驗證已通過：source_to_mount。
- Skill 4 自動化驗證已通過：mount_to_s3。

## 尚未驗證或證據不足

- 可歸因實際帳務成本尚未由 Cost Explorer、Billing 或 CUR artifact 證實；不得以 runtime 估算代替。

## 後續提醒

- Skill 4 must resolve a candidate-specific registered PoC recipe before deployment.
- The standard small-cost ceiling and cleanup guarantee must pass before deployment.

## 證據帳本

| 敘述 | 類型 | 狀態 | 證據 |
| --- | --- | --- | --- |
| 候選技術的公開來源 | source-backed fact | recorded | https://aws.amazon.com/tw/blogs/aws/launching-s3-files-making-s3-buckets-accessible-as-file-systems/ |
| recipe | runtime evidence | s3_files_cdk | S4 runtime artifact |
| source_to_mount | runtime evidence | verified | S4 runtime artifact |
| mount_to_s3 | runtime evidence | verified | S4 runtime artifact |
| ssm_status | runtime evidence | Success | S4 runtime artifact |
| PoC 成本估算 | public list-price estimate | estimated | POC-QUOTE-4C820F98175B |
| PoC 可歸因實際帳務成本 | AWS billing evidence | pending | No attributable AWS Billing, Cost Explorer, or CUR artifact was provided. |
