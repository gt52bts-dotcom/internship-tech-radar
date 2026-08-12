# Skill 5 Report｜把 PoC 結果整理成主管能判斷的證據報告

## 一句話定位

Skill 5 是「證據結案報告」。它把 Skill 1 到 Skill 4 的來源、評分、成本、PoC runtime、資源盤點、cleanup 和限制整理成一份可交給主管看的技術決策報告。

## 報告畫面應該展出什麼

| 報告區塊 | 主管看到的內容 | 作用 |
|---|---|---|
| 結論摘要 | 這案是 validated and cleaned、blocked before PoC，或 awaiting company validation。 | 先講決策狀態，不讓主管在細節裡找答案。 |
| 來源與技術意義 | AWS 新聞到底提供什麼新能力，對公司可能有什麼價值。 | 連回原始需求，避免 PoC 變成孤立實驗。 |
| Skill 3 評估 | 分數、權重、成本預估、推薦或停止原因。 | 說明為什麼當初進或不進 Skill 4。 |
| Skill 4 驗證 | 部署方式、成功條件、runtime evidence、人工 review、cleanup。 | 用實際證據支撐「成功」兩個字。 |
| 資源與權限盤點 | 建了哪些 AWS resource、碰了哪些 IAM / API action、是否符合報價預期。 | 讓成本、治理與安全邊界可檢查。 |
| 未驗證事項 | 例如正式帳務、公司 production 環境、長時間效能、主管最終採納。 | 防止過度宣稱。 |

## Lambda 報告可以怎麼展示

| 項目 | Lambda 案例內容 |
|---|---|
| 技術命題 | Lambda 能否直接 reference 自管 S3 code package。 |
| Skill 3 成本口徑 | 依 AWS 官方 Lambda request、duration / GB-second 與 S3 storage / request 計價公式估算。 |
| 預估成本 | expected 約 USD 0.000749，high 約 USD 0.003387，建議核准上限 USD 0.05。 |
| PoC 結果 | CloudFormation 建立成功，Lambda 保留 REFERENCE 設定，invoke 成功。 |
| 報告結論 | 技術可行並完成 cleanup，但 production 採用仍需看公司部署流程與治理規則。 |

這種寫法的亮點是：主管不需要相信 AI 的口頭保證，只要看報告就知道「來源說了什麼、成本怎麼估、實際驗了什麼、還有哪些沒有驗」。

## S3 Files 報告可以怎麼展示

| 項目 | S3 Files 案例內容 |
|---|---|
| 技術命題 | S3 bucket 是否能以 file system 型態被 EC2 mount 使用。 |
| PoC 資源 | 19 個 CloudFormation resources，包含 S3 Files、S3、EC2、VPC、Security Group、IAM。 |
| 驗證結果 | S3 到 mount、mount 到 S3 兩個方向都完成資料讀寫驗證。 |
| 權限盤點 | 29 個 action，涵蓋 CloudFormation、EC2、IAM、S3、S3 Files、SSM。 |
| 報價對帳 | 實際部署資源與報價預期一致，沒有漏列實際會建立的資源。 |
| 報告結論 | validated and cleaned，可作為完整成功案例展示。 |

S3 Files 報告特別適合拿來說明 Skill 5 的價值，因為它不只說「PoC 有過」，還能展出資源、權限、資料流與 cleanup 的完整證據鏈。

## 停止案例報告怎麼寫

| 案例 | Skill 5 應呈現的結論 |
|---|---|
| WorkSpaces AI Agents | 停在 Skill 3；原因是完整 agent session 的成本與合規邊界較重，phase 1 infrastructure 能證明的決策增量有限。 |
| Quick Suite | 停在 Skill 3；原因是官方新聞多為產品宣稱，缺少足夠的最小實作做法與 deployable recipe。 |

停止案例的報告會寫清楚「不建議進 PoC 的原因」。這讓主管看到 AI 雷達能找新技術，也能節省不值得投入的測試時間與雲端成本。

## 投影片可放的重點

| 主管會關心的問題 | Skill 5 給的答案 |
|---|---|
| 這個專案最後留下什麼？ | 每個案例都有可追溯的來源、評估、成本、驗證與結案狀態。 |
| 成功案例怎麼證明成功？ | 用 runtime evidence、資源盤點、權限盤點與 cleanup 回查，不只用文字描述。 |
| 停止案例有沒有價值？ | 有。它們證明流程能擋下不值得硬做的 PoC，節省時間和成本。 |
