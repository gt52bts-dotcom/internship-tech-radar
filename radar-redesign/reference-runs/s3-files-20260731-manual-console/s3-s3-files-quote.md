# Skill 3 PoC 報價單：Launching S3 Files, making S3 buckets accessible as file systems | AWS News Blog

- Quote ID：POC-QUOTE-C4ECB392A212
- 狀態：已完成估算
- Run ID：direct-url-20260731-f1baf62f
- Candidate ID：S1-65801FA11243
- 目標區域：ap-southeast-1
- 報價性質：非正式公開牌價估算
- 即時 AWS Pricing API：否
- 正式採購報價：否
- 有效期限：2026-08-07

- 預期費用 USD：0.04719
- 低/中/高情境 USD：0.018037 / 0.04719 / 0.150962
- 建議核准上限 USD：0.2
- Recipe：s3_files_cdk

## 明細

- EC2 t3.micro Linux on-demand: qty=2 hours, rate=0.0132 USD/instance-hour, subtotal=0.0264 USD
- EBS gp3 storage: qty=0.021917808219178082 GB-month, rate=0.096 USD/GB-month, subtotal=0.002104 USD
- S3 Files active storage: qty=0.000273972602739726 GB-month, rate=0.36 USD/GB-month, subtotal=9.9e-05 USD
- S3 Files write access: qty=0.1 GB, rate=0.06 USD/GB, subtotal=0.006 USD
- S3 Files export/read access: qty=0.1 GB, rate=0.03 USD/GB, subtotal=0.003 USD
- S3 Files small read access: qty=0.1 GB, rate=0.03 USD/GB, subtotal=0.003 USD
- S3 Files import/write access: qty=0.1 GB, rate=0.06 USD/GB, subtotal=0.006 USD
- S3 Standard storage: qty=0.000273972602739726 GB-month, rate=0.025 USD/GB-month, subtotal=7e-06 USD
- S3 PUT/COPY/POST/LIST requests: qty=100 requests, rate=5e-06 USD/request, subtotal=0.0005 USD
- S3 GET requests: qty=200 requests, rate=4e-07 USD/request, subtotal=8e-05 USD

## 來源

- AWS public EC2 price file, Asia Pacific (Singapore): https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/Asia%20Pacific%20(Singapore)/Linux/index.json
- AWS public EBS pricing, Asia Pacific (Singapore): https://aws.amazon.com/ebs/pricing/
- AWS S3 Files public pricing example rate: https://aws.amazon.com/s3/pricing/
- AWS Price List files/rate card interpretation: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/finding-prices-in-service-price-list-files.html
