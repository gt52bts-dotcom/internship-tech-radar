# 技術驗證報告｜Build an Amazon Connect Customer Data Lake with a Reusable CDK Construct | AWS Contact Center

- 報告狀態：階段性報告
- Run ID：direct-url-20260731-766826d4
- 來源：https://aws.amazon.com/blogs/contact-center/build-an-amazon-connect-customer-data-lake-with-a-reusable-cdk-construct/

## 一句結論

> Skill 3 已完成 PoC 預估報價，建議進入實際 Skill 4 受控付費 PoC；仍須具名人員完成部署授權，且尚無 runtime 證據。

## 評估摘要

| 指標 | 結果 |
| --- | --- |
| Skill 3 加權分 | 3.75 |
| 信心 | 中等 |
| 區域狀態 | 區域支援尚未確認 |
| 建議進入實際 Skill 4 PoC | 是 |
| 成本 | 已完成估算 |

## PoC 成本估算報價單

- Quote ID：POC-QUOTE-D457A8453933
- 區域：ap-southeast-1
- 幣別：USD
- 價格快照：2026-07-31
- 有效期限：2026-08-07
- 情境總額：低 **$0.000593**／預期 **$0.003246**／高 **$0.032075**
- 建議核准上限：**$0.05**
- 報價性質：非正式公開牌價估算；即時 Pricing API：否

### 預期情境明細

| 項目 | 費率 | 用量 | 小計 USD |
| --- | ---: | ---: | ---: |
| Lambda requests | 0.0000002 USD/request | 100 requests | 0.00002 |
| Lambda x86 duration | 0.000016667 USD/GB-second | 5 GB-seconds | 0.000083 |
| CloudWatch Logs ingestion | 0.5 USD/GB ingested | 0.005 GB ingested | 0.0025 |
| S3 Standard storage | 0.025 USD/GB-month | 0.000136986 GB-month | 0.000003 |
| S3 PUT/COPY/POST/LIST requests | 0.000005 USD/request | 100 requests | 0.0005 |
| S3 GET requests | 0.0000004 USD/request | 100 requests | 0.00004 |
| Glue Data Catalog metadata objects | 0.00001 USD/object-month | 0.02739726 object-month | 0.00 |
| Glue Data Catalog API requests | 0.000001 USD/request | 100 requests | 0.0001 |
| **預期總額** |  |  | **0.003246** |

### 報價假設與限制

- 預期情境假設：詳見情境明細。
- Tax, private pricing, Savings Plans, credits, enterprise discounts, and Free Tier are excluded.
- This quote must be regenerated if the public pricing page changes or the quote expires.
- Actual billing must be checked separately after Skill 4, using Billing/Cost Explorer/CUR evidence when attributable.
- Service dimensions not detected by S2/IaC are excluded.
- Provisioned capacity, NAT/data transfer, long-running compute, managed ingestion pipelines, and downstream analytics are excluded unless detected and modeled.
- Use AWS Pricing Calculator, CloudFormation estimate-template-cost, Infracost, or AWS Price List API for a stronger quote before a larger PoC.
- 這是 PoC 前的非正式公開牌價估算，用於 Skill 3 審查與 Skill 4 小額上限控管。它不是 AWS 帳單、正式採購報價，也未套用稅務、折扣、credits、Free Tier 或公司私有價格。

### 官方價格來源

- [Amazon CloudWatch Logs public ingestion price example](https://aws.amazon.com/cloudwatch/pricing/)
- [AWS Glue Data Catalog marginal storage price after free tier](https://aws.amazon.com/glue/pricing/)
- [AWS Lambda public request price](https://aws.amazon.com/lambda/pricing/)
- [AWS public S3 Standard storage price snapshot, Asia Pacific (Singapore)](https://aws.amazon.com/s3/pricing/)
- [AWS Price List files/rate card interpretation](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/finding-prices-in-service-price-list-files.html)
- [Future Level B enhancement: query current SKU prices programmatically](https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_pricing_GetProducts.html)
- [Future Level B enhancement: estimate monthly cost from CloudFormation templates](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_EstimateTemplateCost.html)
- [Manual cross-check and formal estimate workflow](https://docs.aws.amazon.com/pricing-calculator/)

## 預估成本 vs 可歸因實際帳務成本

| 項目 | 狀態 | 金額 USD | 證據 |
| --- | --- | ---: | --- |
| Skill 3 公開牌價估算 | 已完成估算 | 0.003246 | POC-QUOTE-D457A8453933 |
| 可歸因實際帳務成本 | 待補實際帳務證據 | 未記錄 | 無可用資料 |
| 差異（實際 - 預估） | 待補實際成本 | 未記錄 | Actual cost is shown only when an attributable AWS Billing, Cost Explorer, or CUR artifact records it; runtime duration is not converted into actual cost. |

- 實際成本狀態：待補實際帳務證據。No attributable AWS Billing, Cost Explorer, or CUR artifact was provided.
- 不以 EC2 執行時間、CloudFormation 狀態或 runtime artifact 推算實際 AWS 帳務成本。

## 技術驗證

| 檢查 | 狀態 |
| --- | --- |
| Skill 4 validation | 等待 PoC 授權 |
| CloudFormation | 未記錄 |
| 自動化驗證 | 未記錄 |
| AWS Console review | 未記錄 |
| Console 截圖證據 | 未記錄 |
| cleanup | 不適用，未建立雲端資源 |

## 已證實的事實

- 官方來源已記錄：https://aws.amazon.com/blogs/contact-center/build-an-amazon-connect-customer-data-lake-with-a-reusable-cdk-construct/
- Skill 3 加權分已依固定 rubric 計算：3.75
- PoC 成本估算報價單已建立：POC-QUOTE-D457A8453933，預期 USD 0.003246。

## 尚未驗證或證據不足

- No candidate-relevant official AWS pricing page was fetched in this S2 run.
- No candidate-relevant official AWS Region or availability page was fetched in this S2 run.
- 報價單是公開牌價估算；實際 AWS 費用需在部署後以帳務資料核對。
- 可歸因實際帳務成本尚未由 Cost Explorer、Billing 或 CUR artifact 證實；不得以 runtime 估算代替。
- AWS Console review 尚未完成或尚未記錄。
- Skill 3 的 PoC 判斷只代表公開技術證據與成本/recipe 條件達標；公司工作負載適配性未評估。
- cleanup 尚未完成或尚未記錄。

## 後續提醒

- Skill 4 must resolve a candidate-specific registered PoC recipe before deployment.
- The standard small-cost ceiling and cleanup guarantee must pass before deployment.

## 證據帳本

| 敘述 | 類型 | 狀態 | 證據 |
| --- | --- | --- | --- |
| 候選技術的公開來源 | source-backed fact | recorded | https://aws.amazon.com/blogs/contact-center/build-an-amazon-connect-customer-data-lake-with-a-reusable-cdk-construct/ |
| PoC 成本估算 | public list-price estimate | 已完成估算 | POC-QUOTE-D457A8453933 |
| PoC 可歸因實際帳務成本 | AWS billing evidence | 待補實際帳務證據 | No attributable AWS Billing, Cost Explorer, or CUR artifact was provided. |
