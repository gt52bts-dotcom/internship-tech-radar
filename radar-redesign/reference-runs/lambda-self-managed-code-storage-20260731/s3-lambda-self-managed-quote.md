# Skill 3 PoC 報價單：AWS Lambda 宣布自主管理程式碼儲存空間 - AWS

- Quote ID：POC-QUOTE-D3255FE85969
- 狀態：已完成估算
- Run ID：direct-url-20260731-ae6e8775
- Candidate ID：S1-C7ED2885BADB
- 目標區域：ap-southeast-1
- 報價性質：非正式公開牌價估算
- 即時 AWS Pricing API：否
- 正式採購報價：否
- 有效期限：2026-08-07

- 預期費用 USD：0.000249
- 低/中/高情境 USD：7.2e-05 / 0.000249 / 0.000886
- 建議核准上限 USD：0.05
- Recipe：lambda_self_managed_s3_code_storage_cdk

## 明細

- Lambda requests: qty=15 requests, rate=2e-07 USD/request, subtotal=3e-06 USD
- Lambda x86 duration: qty=5 GB-seconds, rate=1.66667e-05 USD/GB-second, subtotal=8.3e-05 USD
- S3 Standard storage: qty=2.7397260273972603e-05 GB-month, rate=0.025 USD/GB-month, subtotal=1e-06 USD
- S3 PUT/COPY/POST/LIST requests: qty=30 requests, rate=5e-06 USD/request, subtotal=0.00015 USD
- S3 GET requests: qty=30 requests, rate=4e-07 USD/request, subtotal=1.2e-05 USD

## 來源

- AWS Lambda public request price: https://aws.amazon.com/lambda/pricing/
- AWS public S3 Standard storage price snapshot, Asia Pacific (Singapore): https://aws.amazon.com/s3/pricing/
- AWS Price List files/rate card interpretation: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/finding-prices-in-service-price-list-files.html
