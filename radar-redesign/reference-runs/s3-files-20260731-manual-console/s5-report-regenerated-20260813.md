# Skill 5 PoC 結案報告：Launching S3 Files, making S3 buckets accessible as file systems | AWS News Blog

## 一眼看重點

- 結論：本次受控 PoC 已完成、已人工確認，並已清除資源。
- 做完發現：S3 Files 在本次帳號與地區中可以被建立，且 EC2 掛載點和 S3 bucket 之間能做最小讀寫驗證。
- 對公司的意義：這代表它不只是新聞功能，而是有機會讓需要檔案介面的工作負載共用 S3 資料；下一步要判斷它是否撐得住真實檔案型工作負載。
- 現在不能宣稱：這不是正式生產環境驗證，不能宣稱可直接導入公司正式系統。

## 帳號、地區、權限能不能用

| 問題 | 結論 | 證據 |
| --- | --- | --- |
| 我們的 AWS 帳號可以建立這個 PoC 嗎？ | 可以，已成功建立本次 PoC 所需資源。 | CloudFormation 建立完成。 |
| 指定地區可以使用嗎？ | 可以，本次使用 ap-southeast-1。 | 同一地區完成部署與驗證。 |
| 權限夠不夠？ | 夠，至少足以完成本次最小 PoC。 | 資源建立成功，且核心驗證通過。 |
| 資源有沒有收乾淨？ | 已清除並回查。 | CloudFormation stack 已刪除；測試 bucket 已先清空；清除範圍符合本次測試前綴。 |

## 我實際做完了什麼

- 整理官方來源，確認這個功能想解決的技術問題。
- 用固定評分準則完成 Skill 3 評估，分數為 4.4 / 5。
- 用公開價格建立小型 PoC 成本估算：預期約 USD 0.04719，核准上限 USD 0.20。
- 在 ap-southeast-1 建立受控 PoC 環境。
- 跑完核心驗證：S3 內的物件可以從 EC2 掛載點讀到；從掛載點寫入的檔案可以回到 S3；EC2 測試指令可以透過受控方式執行成功。
- 完成 AWS Console 人工確認。
- 完成受控清除，避免測試資源繼續產生成本。

## 這次 PoC 證明了什麼

- S3 內的物件可以從 EC2 掛載點讀到
- 從掛載點寫入的檔案可以回到 S3
- EC2 測試指令可以透過受控方式執行成功

## 成本與清除狀態

- 預估成本：預期約 USD 0.04719，核准上限 USD 0.20
- 成本性質：這是部署前用公開價格估算，不是 AWS 帳單。
- 清除狀態：已清除並回查。
- 價格來源：AWS 官方公開定價頁。

## 還不能拿來宣稱的事

- 這不是正式生產環境驗證，不能宣稱可直接導入公司正式系統。
- 這次只證明最小 PoC 路徑可行，尚未測效能、可靠性、長時間運作或多人使用。
- 尚未證明同步延遲、POSIX 權限、一致性與錯誤復原是否符合真實工作負載。
- 預估成本不是 AWS 帳單，不能拿來宣稱實際花費。

## 下一步要補的決策證據

- 補一個小型真實工作負載測試：多檔案讀寫、同步延遲、權限錯誤與掛載失敗復原。
- 外部查 S3 Files 的限制、定價與 troubleshooting，判斷它適合檔案共享、資料湖前處理，還是只適合展示型 PoC。

## 相關文章與應用實例

- 證據邊界：此節把已取得來源與待外搜文章分開；待外搜項目不是已驗證結論，找到來源後必須回填到 S1/S2/S3 才能升級為證據。

### 相關文章

- Launching S3 Files, making S3 buckets accessible as file systems | AWS News Blog 原始來源文章（已取得來源）：https://aws.amazon.com/tw/blogs/aws/launching-s3-files-making-s3-buckets-accessible-as-file-systems/
  - 為什麼要看：這是本次 S1-S5 證據鏈的起點，只能支持原文已明確寫出的主張。
  - 會交給誰用：預言者雷達
- S3 Files 官方實作文件或 workshop（待外部搜尋）：搜尋：`S3 Files EC2 mount workload migration NFS S3 bucket architecture`
  - 為什麼要看：補足原始新聞沒有講清楚的部署步驟、架構限制與操作條件。
  - 會交給誰用：架構師 / 驗證者
- S3 Files 權限、治理與 rollback 案例（待外部搜尋）：搜尋：`S3 Files IAM access point mount target VPC security group permissions`
  - 為什麼要看：判斷它能不能從展示型 PoC 進到受控導入，尤其是 IAM、Region、cleanup 與回復策略。
  - 會交給誰用：治理者 / 驗證者

### 應用實例

- 把既有 EC2 檔案讀寫工作負載接到 S3 bucket
  - 怎麼用在本案例：用 S3 Files mount 方式讓應用程式先維持檔案系統介面，再觀察同步、延遲與一致性限制。
  - 會改變的判斷：決定下一輪要測真實檔案操作情境，不只是證明 EC2 可以 mount。
  - 下一個角色：驗證者
- 資料湖前處理或批次匯入暫存區
  - 怎麼用在本案例：讓工具用檔案介面寫入資料，再回到 S3 bucket 做後續分析或治理。
  - 會改變的判斷：判斷 S3 Files 適合過渡型整合，還是應直接改寫成原生 S3 API。
  - 下一個角色：架構師

## 官方來源

- https://aws.amazon.com/tw/blogs/aws/launching-s3-files-making-s3-buckets-accessible-as-file-systems/
