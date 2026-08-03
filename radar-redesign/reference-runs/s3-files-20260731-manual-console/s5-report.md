# 技術驗證報告｜Launching S3 Files, making S3 buckets accessible as file systems | AWS News Blog

- 報告狀態：最終報告
- Run ID：direct-url-20260731-f1baf62f
- 來源：https://aws.amazon.com/tw/blogs/aws/launching-s3-files-making-s3-buckets-accessible-as-file-systems/

## 新聞摘要：應用面優勢

> 新聞指出：Amazon S3 Files makes S3 buckets accessible as high-performance file systems on AWS compute resources, eliminating the tradeoff between object storage benefits and interactive file capabilities while enabling seamless data sharing with ~1ms latencies.

## 評估摘要

| 指標 | 結果 |
| --- | --- |
| Skill 3 加權分（滿分 5） | 4.4 / 5 |
| 區域狀態 | 新加坡區域可用 |
| 建議進入實際 Skill 4 PoC | 是 |
| 成本 | 已完成估算 |

## PoC 成本估算報價單

- Quote ID：POC-QUOTE-C4ECB392A212
- 區域：ap-southeast-1
- 幣別：USD
- 價格快照：2026-07-30
- 有效期限：2026-08-07
- 情境總額：低 **$0.018037**／預期 **$0.04719**／高 **$0.150962**
- 建議核准上限：**$0.20**
- 報價性質：非正式公開牌價估算；即時 Pricing API：否
- 計價口徑：月費型資源以每月價格為基礎，再依 PoC 使用時數折算；EC2 等運算資源依啟用小時計算；請求型項目依實際請求量增加
- 預期情境假設：2 小時、0.1 GB active storage。
- 人工需確認的 PoC 資源：EC2 t3.micro Linux on-demand、EBS gp3 storage、S3 Files active storage、S3 Files write access、S3 Files export/read access、S3 Files small read access、S3 Files import/write access、S3 Standard storage。
- 主要成本驅動：預期情境中最高的是 EC2 t3.micro Linux on-demand（USD 0.0264）；當 hours x USD/instance-hour 增加時，這項費用會上升。

### 預期情境明細

| 項目 | 費率 | 用量 | 小計 USD |
| --- | ---: | ---: | ---: |
| EC2 t3.micro Linux on-demand | 0.0132 USD/instance-hour | 2 hours | 0.0264 |
| EBS gp3 storage | 0.096 USD/GB-month | 0.021917808 GB-month | 0.002104 |
| S3 Files active storage | 0.36 USD/GB-month | 0.000273973 GB-month | 0.000099 |
| S3 Files write access | 0.06 USD/GB | 0.1 GB | 0.006 |
| S3 Files export/read access | 0.03 USD/GB | 0.1 GB | 0.003 |
| S3 Files small read access | 0.03 USD/GB | 0.1 GB | 0.003 |
| S3 Files import/write access | 0.06 USD/GB | 0.1 GB | 0.006 |
| S3 Standard storage | 0.025 USD/GB-month | 0.000273973 GB-month | 0.000007 |
| S3 PUT/COPY/POST/LIST requests | 0.000005 USD/request | 100 requests | 0.0005 |
| S3 GET requests | 0.0000004 USD/request | 200 requests | 0.00008 |
| **預期總額** |  |  | **0.04719** |

### 官方價格來源

- [AWS public EC2 price file, Asia Pacific (Singapore)](https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/Asia%20Pacific%20(Singapore)/Linux/index.json)
- [AWS public EBS pricing, Asia Pacific (Singapore)](https://aws.amazon.com/ebs/pricing/)
- [AWS S3 Files public pricing example rate](https://aws.amazon.com/s3/pricing/)
- [AWS Price List files/rate card interpretation](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/finding-prices-in-service-price-list-files.html)

## 預估成本 vs 可歸因實際帳務成本

| 項目 | 狀態 | 金額 USD | 證據 |
| --- | --- | ---: | --- |
| Skill 3 公開牌價估算 | 已完成估算 | 0.04719 | POC-QUOTE-C4ECB392A212 |
| 可歸因實際帳務成本 | 待補實際帳務證據 | 未記錄 | 無可用資料 |
| 差異（實際 - 預估） | 待補實際成本 | 未記錄 | Actual cost is shown only when an attributable AWS Billing, Cost Explorer, or CUR artifact records it; runtime duration is not converted into actual cost. |

- 實際成本狀態：待補實際帳務證據。No attributable AWS Billing, Cost Explorer, or CUR artifact was provided.
- 不以 EC2 執行時間、CloudFormation 狀態或 runtime artifact 推算實際 AWS 帳務成本。

## cleanup 前即時用量快照

- 快照狀態：已擷取
- 擷取時間：2026-07-31T08:05:24.920276+00:00
- 建立到 cleanup 前經過：約 4.3 分鐘
- 性質：這是 runtime facts，不是 AWS 帳單；實際成本仍需 Billing、Cost Explorer 或 CUR artifact。

| 類別 | cleanup 前看到的證據 |
| --- | --- |
| CloudFormation | 狀態 CREATE_COMPLETE；資源數 19；tags 0 |
| S3 | current objects 3；versions 3；delete markers 0；size bytes 188；tags 5 |
| EC2 | instance i-0f09f7e67fcc6849f；state running；type t3.micro；tags 4 |

## 技術驗證

| 檢查 | 狀態 |
| --- | --- |
| Skill 4 validation | PoC 可由人類授權啟動 |
| CloudFormation | CloudFormation 建立完成 |
| 自動化驗證 | 已驗證, 已驗證, Success |
| AWS Console review | 已確認 |
| Console 截圖證據 | 已截圖並經人類確認（1 張） |
| cleanup | 已驗證 |

### 技術驗證狀態

- 官方來源已記錄：https://aws.amazon.com/tw/blogs/aws/launching-s3-files-making-s3-buckets-accessible-as-file-systems/
- Skill 3 加權分已依固定 rubric 計算：4.4
- PoC 成本估算報價單已建立：POC-QUOTE-C4ECB392A212，預期 USD 0.04719。
- CloudFormation stack 已達 CREATE_COMPLETE。
- AWS Console review 已以 1 張截圖透過 GUI 或對話交由具名人員確認。
- cleanup 前即時用量快照已記錄：已擷取；這是 runtime facts，不是 AWS 帳單。
- Skill 4 自動化驗證已通過：source_to_mount。
- Skill 4 自動化驗證已通過：mount_to_s3。

## 尚未驗證或證據不足

- 可歸因實際帳務成本尚未由 Cost Explorer、Billing 或 CUR artifact 證實；不得以 runtime 估算代替。
- Skill 3 的 PoC 判斷只代表公開技術證據與成本/recipe 條件達標；公司工作負載適配性未評估。

## Future work

- 補上可歸因的 Cost Explorer、Billing 或 CUR artifact，讓 Skill 5 能比較預估成本與實際帳務成本。
- 用同一篇新聞的應用面優勢設計第二輪 PoC 問題，例如增加資料量、併發、錯誤情境或觀測指標，而不是只證明資源能建立。
- 把這個候選對應到一個明確的人類工作場景，補上目前做法、痛點、量測指標與導入後預期改善。
- 整理成 final proposal / 論文可引用的案例：問題、方法、證據鏈、限制、價值與下一步。

## Reviewer questions

- 這篇新聞提到的新功能，最適合改善哪一個真實使用者流程？現有流程的 baseline 是什麼？
- Skill 1 到 Skill 5 的每個結論分別由哪個 artifact 支撐？哪些只是推論或待驗證？
- 報價單中哪一項最貴？預期情境中最高的是 EC2 t3.micro Linux on-demand（USD 0.0264）；當 hours x USD/instance-hour 增加時，這項費用會上升；什麼實際使用情境會讓它增加？
- PoC 會建立哪些 AWS 資源？人類是否已確認這些資源、Region、成本上限與 cleanup 範圍？
- 這次 PoC 只驗證功能可行，還是也驗證效能、可靠性、權限治理與可維運性？
- 實際成本何時能用 Cost Explorer、Billing 或 CUR 歸因到這個 run？若不能歸因，報告要如何標示限制？

## 延伸閱讀關鍵字

- S3 Files
- S3
- EC2
- EFS
- VPC
- Lambda
- storage
- serverless
- networking
- ci cd
- infrastructure
- AWS Pricing Calculator
- Cost Explorer
- CloudFormation
- PoC cleanup
- Future work

## S1-S5 階段證據

| 階段 | 狀態 | 證據 |
| --- | --- | --- |
| S1 Scan | scanned_with_gaps | candidate_count=1；external_fetch=是；source=https://aws.amazon.com/tw/blogs/aws/launching-s3-files-making-s3-buckets-accessible-as-file-systems/ |
| S2 Compare | ready_for_human_shortlist | candidate_count=1；linked_evidence=7；region=新加坡區域可用 |
| S3 Evaluate | evaluated | score=4.4 / 5；quote=POC-QUOTE-C4ECB392A212；recommend_poc=是 |
| S4 Validate | PoC 可由人類授權啟動 | runtime=清除已驗證；cloudformation=CloudFormation 建立完成；checks=已驗證, 已驗證, Success |
| S4 Cleanup | 已驗證 | cleanup=已驗證；usage_snapshot=已擷取 |
| S5 Report | 最終報告 | report_type=最終報告；actual_cost=待補實際帳務證據 |

## 證據來源表

| 敘述 | 類型 | 狀態 | 證據 |
| --- | --- | --- | --- |
| 候選技術的公開來源 | source-backed fact | recorded | https://aws.amazon.com/tw/blogs/aws/launching-s3-files-making-s3-buckets-accessible-as-file-systems/ |
| recipe | runtime evidence | s3_files_cdk | S4 runtime artifact |
| source_to_mount | runtime evidence | 已驗證 | S4 runtime artifact |
| mount_to_s3 | runtime evidence | 已驗證 | S4 runtime artifact |
| ssm_status | runtime evidence | Success | S4 runtime artifact |
| Infrastructure Composer Console review | human-reviewed screenshot evidence | 已確認 | S4 Console review evidence (1 screenshot metadata records) |
| PoC 成本估算 | public list-price estimate | 已完成估算 | POC-QUOTE-C4ECB392A212 |
