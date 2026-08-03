# 技術驗證報告｜AWS Lambda 宣布自主管理程式碼儲存空間 - AWS

- 報告狀態：最終報告
- Run ID：direct-url-20260731-ae6e8775
- 來源：https://aws.amazon.com/tw/about-aws/whats-new/2026/07/lambda-self-managed-code-storage/

## 新聞摘要：應用面優勢

> 新聞指出：AWS Lambda 宣布自主管理程式碼儲存空間 現在支援用於程式碼儲存的自主管理 Amazon S3 儲存貯體，讓您可直接從自己的 S3 儲存貯體參照來源程式碼，無需由 Lambda 建立中繼副本。這項功能可藉由移除複製步驟，消除程式碼儲存空間限制，並縮短函數建立與更新後的啟動時間。 AWS Lambda 是一項無伺服器運算服務，可執行您的程式碼，無需您管理伺服器。部署許多函數及作為 Lambda 層的額外程式碼的客戶，每個區域通常需要超過 75GB 的程式碼儲存空間，因此必須提交支援工單以提高此配額。…

## 評估摘要

| 指標 | 結果 |
| --- | --- |
| Skill 3 加權分（滿分 5） | 4.15 / 5 |
| 區域狀態 | 新加坡區域可用 |
| 建議進入實際 Skill 4 PoC | 是 |
| 成本 | 已完成估算 |

## PoC 成本估算報價單

- Quote ID：POC-QUOTE-D3255FE85969
- 區域：ap-southeast-1
- 幣別：USD
- 價格快照：2026-07-31
- 有效期限：2026-08-07
- 情境總額：低 **$0.000072**／預期 **$0.000249**／高 **$0.000886**
- 建議核准上限：**$0.05**
- 報價性質：非正式公開牌價估算；即時 Pricing API：否
- 計價口徑：月費型資源以每月價格為基礎，再依 PoC 使用時數折算；Lambda 只有被呼叫時才計請求數與執行時間/記憶體用量；請求型項目依實際請求量增加
- 預期情境假設：1 小時、0.02 GB artifact、15 次 Lambda request、5 GB-seconds。
- 人工需確認的 PoC 資源：Lambda requests、Lambda x86 duration、S3 Standard storage、S3 PUT/COPY/POST/LIST requests、S3 GET requests。
- 主要成本驅動：預期情境中最高的是 S3 PUT/COPY/POST/LIST requests（USD 0.00015）；當 PUT/COPY/POST/LIST count x USD/request 增加時，這項費用會上升。

### 預期情境明細

| 項目 | 費率 | 用量 | 小計 USD |
| --- | ---: | ---: | ---: |
| Lambda requests | 0.0000002 USD/request | 15 requests | 0.000003 |
| Lambda x86 duration | 0.000016667 USD/GB-second | 5 GB-seconds | 0.000083 |
| S3 Standard storage | 0.025 USD/GB-month | 0.000027397 GB-month | 0.000001 |
| S3 PUT/COPY/POST/LIST requests | 0.000005 USD/request | 30 requests | 0.00015 |
| S3 GET requests | 0.0000004 USD/request | 30 requests | 0.000012 |
| **預期總額** |  |  | **0.000249** |

### 官方價格來源

- [AWS Lambda public request price](https://aws.amazon.com/lambda/pricing/)
- [AWS public S3 Standard storage price snapshot, Asia Pacific (Singapore)](https://aws.amazon.com/s3/pricing/)
- [AWS Price List files/rate card interpretation](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/finding-prices-in-service-price-list-files.html)

## 預估成本 vs 可歸因實際帳務成本

| 項目 | 狀態 | 金額 USD | 證據 |
| --- | --- | ---: | --- |
| Skill 3 公開牌價估算 | 已完成估算 | 0.000249 | POC-QUOTE-D3255FE85969 |
| 可歸因實際帳務成本 | 待補實際帳務證據 | 未記錄 | 無可用資料 |
| 差異（實際 - 預估） | 待補實際成本 | 未記錄 | Actual cost is shown only when an attributable AWS Billing, Cost Explorer, or CUR artifact records it; runtime duration is not converted into actual cost. |

- 實際成本狀態：待補實際帳務證據。No attributable AWS Billing, Cost Explorer, or CUR artifact was provided.
- 不以 EC2 執行時間、CloudFormation 狀態或 runtime artifact 推算實際 AWS 帳務成本。

## cleanup 前即時用量快照

- 狀態：未記錄。
- 說明：這不影響 cleanup 結論，但 Skill 5 無法列出刪除前的即時用量證據。

## 技術驗證

| 檢查 | 狀態 |
| --- | --- |
| Skill 4 validation | PoC 可由人類授權啟動 |
| CloudFormation | CloudFormation 建立完成 |
| 自動化驗證 | 已驗證 |
| AWS Console review | 已確認 |
| Console 截圖證據 | 已截圖並經人類確認（1 張） |
| cleanup | 已驗證 |

### 技術驗證狀態

- 官方來源已記錄：https://aws.amazon.com/tw/about-aws/whats-new/2026/07/lambda-self-managed-code-storage/
- Skill 3 加權分已依固定 rubric 計算：4.15
- PoC 成本估算報價單已建立：POC-QUOTE-D3255FE85969，預期 USD 0.000249。
- CloudFormation stack 已達 CREATE_COMPLETE。
- AWS Console review 已以 1 張截圖透過 GUI 或對話交由具名人員確認。
- Skill 4 自動化驗證已通過：cloudformation_reference_mode。
- Skill 4 自動化驗證已通過：lambda_invoke。

## 尚未驗證或證據不足

- No candidate-relevant official AWS pricing page was fetched in this S2 run.
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
- 報價單中哪一項最貴？預期情境中最高的是 S3 PUT/COPY/POST/LIST requests（USD 0.00015）；當 PUT/COPY/POST/LIST count x USD/request 增加時，這項費用會上升；什麼實際使用情境會讓它增加？
- PoC 會建立哪些 AWS 資源？人類是否已確認這些資源、Region、成本上限與 cleanup 範圍？
- 這次 PoC 只驗證功能可行，還是也驗證效能、可靠性、權限治理與可維運性？
- 實際成本何時能用 Cost Explorer、Billing 或 CUR 歸因到這個 run？若不能歸因，報告要如何標示限制？

## 延伸閱讀關鍵字

- Lambda
- S3
- CloudFormation
- storage
- serverless
- infrastructure
- AWS Pricing Calculator
- Cost Explorer
- PoC cleanup
- Future work

## S1-S5 階段證據

| 階段 | 狀態 | 證據 |
| --- | --- | --- |
| S1 Scan | scanned_with_gaps | candidate_count=1；external_fetch=是；source=https://aws.amazon.com/tw/about-aws/whats-new/2026/07/lambda-self-managed-code-storage/ |
| S2 Compare | ready_for_human_shortlist | candidate_count=1；linked_evidence=1；region=新加坡區域可用 |
| S3 Evaluate | evaluated | score=4.15 / 5；quote=POC-QUOTE-D3255FE85969；recommend_poc=是 |
| S4 Validate | PoC 可由人類授權啟動 | runtime=清除已驗證；cloudformation=CloudFormation 建立完成；checks=已驗證 |
| S4 Cleanup | 已驗證 | cleanup=已驗證；usage_snapshot=未記錄 |
| S5 Report | 最終報告 | report_type=最終報告；actual_cost=待補實際帳務證據 |

## 證據來源表

| 敘述 | 類型 | 狀態 | 證據 |
| --- | --- | --- | --- |
| 候選技術的公開來源 | source-backed fact | recorded | https://aws.amazon.com/tw/about-aws/whats-new/2026/07/lambda-self-managed-code-storage/ |
| recipe | runtime evidence | lambda_self_managed_s3_code_storage_cdk | S4 runtime artifact |
| cloudformation_reference_mode | runtime evidence | 已驗證 | S4 runtime artifact |
| lambda_invoke | runtime evidence | 已驗證 | S4 runtime artifact |
| Infrastructure Composer Console review | human-reviewed screenshot evidence | 已確認 | S4 Console review evidence (1 screenshot metadata records) |
| PoC 成本估算 | public list-price estimate | 已完成估算 | POC-QUOTE-D3255FE85969 |
