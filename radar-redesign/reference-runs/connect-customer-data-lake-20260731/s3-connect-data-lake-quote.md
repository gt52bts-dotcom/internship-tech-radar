# Skill 3 PoC 報價單：Build an Amazon Connect Customer Data Lake with a Reusable CDK Construct | AWS Contact Center

- Quote ID：POC-QUOTE-D457A8453933
- 狀態：已完成估算
- Run ID：direct-url-20260731-766826d4
- Candidate ID：S1-F7F663D036CF
- 目標區域：ap-southeast-1
- 報價性質：非正式公開牌價估算
- 即時 AWS Pricing API：否
- 正式採購報價：否
- 有效期限：2026-08-07

- 預期費用 USD：0.003246
- 低/中/高情境 USD：0.000593 / 0.003246 / 0.032075
- 建議核准上限 USD：0.05
- Recipe：generic_usage_model

## 明細

- Lambda requests: qty=100 requests, rate=2e-07 USD/request, subtotal=2e-05 USD
- Lambda x86 duration: qty=5 GB-seconds, rate=1.66667e-05 USD/GB-second, subtotal=8.3e-05 USD
- CloudWatch Logs ingestion: qty=0.005 GB ingested, rate=0.5 USD/GB ingested, subtotal=0.0025 USD
- S3 Standard storage: qty=0.000136986301369863 GB-month, rate=0.025 USD/GB-month, subtotal=3e-06 USD
- S3 PUT/COPY/POST/LIST requests: qty=100 requests, rate=5e-06 USD/request, subtotal=0.0005 USD
- S3 GET requests: qty=100 requests, rate=4e-07 USD/request, subtotal=4e-05 USD
- Glue Data Catalog metadata objects: qty=0.0273972602739726 object-month, rate=1e-05 USD/object-month, subtotal=0.0 USD
- Glue Data Catalog API requests: qty=100 requests, rate=1e-06 USD/request, subtotal=0.0001 USD

## 來源

- Amazon CloudWatch Logs public ingestion price example: https://aws.amazon.com/cloudwatch/pricing/
- AWS Glue Data Catalog marginal storage price after free tier: https://aws.amazon.com/glue/pricing/
- AWS Lambda public request price: https://aws.amazon.com/lambda/pricing/
- AWS public S3 Standard storage price snapshot, Asia Pacific (Singapore): https://aws.amazon.com/s3/pricing/
- AWS Price List files/rate card interpretation: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/finding-prices-in-service-price-list-files.html
- Future Level B enhancement: query current SKU prices programmatically: https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_pricing_GetProducts.html
- Future Level B enhancement: estimate monthly cost from CloudFormation templates: https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_EstimateTemplateCost.html
- Manual cross-check and formal estimate workflow: https://docs.aws.amazon.com/pricing-calculator/
