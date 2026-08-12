# Skill 4 Validate｜在核准範圍內做最小 AWS PoC

## 一句話定位

Skill 4 是「受控驗證」。只有 Skill 3 已經說清楚要驗證什麼、預估成本多少、成功條件是什麼，並取得人工核准後，才會真的建立 AWS 資源。

## 進 Skill 4 前一定要先看到的核准欄位

| 核准欄位 | Lambda 案例寫法 | 用意 |
|---|---|---|
| PoC 要證明什麼 | Lambda 函數能否用 S3 bucket 作為 self-managed code storage，且 CloudFormation 仍保留 `REFERENCE` 設定。 | 防止 PoC 變成隨便做一個 demo。 |
| 成本上限 | Skill 3 先列低/中/高情境，Lambda 例子的建議核准上限為 USD 0.05。 | 預算要在部署前知道，不是部署後才回頭補。 |
| 成功條件 | CloudFormation `CREATE_COMPLETE`、Lambda 設定為 `S3ObjectStorageMode=REFERENCE`、invoke 成功。 | 驗證結果可明確判定通過或不通過。 |
| 會建立的資源 | versioned S3 bucket、Lambda function、IAM role、bucket policy、CloudWatch Logs。 | 人工核准時先看資源範圍。 |
| 清除方式 | 以同一個 run scope 刪除 CloudFormation stack，並回查資源不存在。 | 避免留下持續計費或權限殘留。 |

## Lambda 成功案例：PoC 驗證畫面

| 驗證點 | 實際證據 |
|---|---|
| 部署方式 | CDK synth 後由 CloudFormation create-stack 建立。 |
| Stack 狀態 | `CREATE_COMPLETE`。 |
| 核心設定 | Lambda function 使用 `S3ObjectStorageMode=REFERENCE`。 |
| Runtime 結果 | Lambda invoke 通過，回傳符合測試 contract。 |
| 後續狀態 | 完成 Console / resource review 後，cleanup 回查已完成。 |

這個 PoC 的價值在於證明官方文件中的新 storage mode 可以在實際帳號中被 CloudFormation 建立、保留設定，並正常執行。

## S3 Files 成功案例：PoC 驗證畫面

| 驗證點 | 實際證據 |
|---|---|
| 部署資源 | CloudFormation 建立 19 個資源，包含 S3 Files file system、mount target、access point、S3 bucket、EC2、VPC、Security Group、IAM role。 |
| 資料面驗證 | S3 API 寫入的 object 可從 EC2 mount 讀取；mount 寫入的檔案可由 S3 API 讀回。 |
| 權限盤點 | 實際觸發 29 個 action，涵蓋 CloudFormation、EC2、IAM、S3、S3 Files、SSM。 |
| 報價對帳 | 實際部署資源與 Skill 3 報價列出的資源一致，沒有 deployed-not-quoted。 |
| 清除結果 | cleanup 回查完成，報告結論為 validated and cleaned。 |

這個 PoC 的價值是把「S3 bucket 可被當作 file system」從產品敘述變成可觀察證據：資源真的建立、mount 真的可用、雙向資料流真的通。

## 失敗案例裡的「硬做」定義

硬做不是指技術上完全不能建任何東西，而是「PoC 證明不了原本要判斷的問題，卻為了展示而硬套一個簡化 demo」。

| 案例 | 如果硬做會變成什麼 | 為什麼不應該做 |
|---|---|---|
| WorkSpaces AI Agents | 只建立 phase 1 infrastructure，甚至開完整 session 來假裝驗證 agent workflow。 | 完整 session 可能產生月費型成本，且不一定能證明公司場景的 AI desktop workflow。 |
| Quick Suite | 找一個相似 AI 工具或簡略 API demo，當成 Quick Suite PoC。 | 官方新聞沒有提供足夠最小架構，demo 會偏離原題，不能代表服務可落地。 |

## 投影片可放的重點

| 主管會關心的問題 | Skill 4 給的答案 |
|---|---|
| AI 會不會亂開雲端資源？ | 不會。Skill 4 需要人工核准、成本上限、成功條件和 cleanup 範圍。 |
| PoC 成功代表什麼？ | 代表一個具體技術命題在 sandbox 被驗證，不代表已可直接上 production。 |
| 為什麼失敗案例不進 PoC？ | 因為 PoC 要能增加決策資訊；如果只是硬湊 demo，反而會誤導主管。 |
