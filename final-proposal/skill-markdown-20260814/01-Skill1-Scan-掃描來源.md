# Skill 1 Scan｜把 AWS 新聞拆成可判斷的技術證據

## 一句話定位

Skill 1 的定位是「證據拆解器」。它把一篇 AWS 官方新聞拆成後面能評分、估成本、決定 PoC 的欄位，先分清楚哪些是 AWS 明講的事，哪些只是可能推論。

## 畫面應該讓人看到什麼

| 報告欄位 | Lambda self-managed code storage 的例子 | 為什麼重要 |
|---|---|---|
| 來源主張 | Lambda 現在可直接參照客戶自己的 S3 bucket 裡的程式碼 package。 | 這是官方明講的新功能，不是 AI 自己想像。 |
| 技術動作 | 建立或更新函數時設定 `S3ObjectStorageMode=REFERENCE`。 | 這句可以直接變成 Skill 4 的驗證條件。 |
| 必要權限 | S3 bucket 要允許 Lambda service principal 讀取 `s3:GetObject` / `s3:GetObjectVersion`。 | PoC 前就知道 IAM 邊界，不會部署後才補猜。 |
| 可能效益 | 少掉 Lambda 複製部署包到 managed storage 的步驟，降低 code storage quota 壓力。 | 這是 business / operation value，但仍需 PoC 驗證。 |
| 待確認問題 | 公司帳號 Region、bucket policy、版本控管與現有部署流程是否相容。 | 這些會進 Skill 2 / Skill 3，不會在 Skill 1 就硬判成功。 |

## Skill 1 真正在做的細節

| 步驟 | 實際處理 | 產出的判斷價值 |
|---|---|---|
| 讀來源 | 解析指定 AWS URL 的標題、時間、服務名稱與正文重點。 | 確認這是 AWS 官方來源，並保留來源可追溯性。 |
| 抽關鍵句 | 把功能描述、使用方式、前提條件、限制與價格句子分開。 | 避免把廣告式效益和可部署做法混在一起。 |
| 標記證據等級 | 區分「來源明講」、「根據來源推論」、「待人工確認」。 | 後面報告能誠實說明信心來源。 |
| 建立候選卡 | 產生 candidate title、related services、implementation hints、possible application contexts。 | Skill 2 才有固定欄位可比較，不是每篇文章各講各的。 |
| 保留疑點 | 記錄缺少 Region、pricing、API、IAM、cleanup 等資訊的缺口。 | 缺口會影響 Skill 3 是否推薦 PoC。 |

## 成功案例怎麼說

Lambda 這案的 Skill 1 很清楚，因為官方文章直接給出做法：設定 `S3ObjectStorageMode=REFERENCE`，並授權 Lambda 讀 S3 object。這代表後面 Skill 4 可以把成功條件寫成「CloudFormation 建立 Lambda 後，函數設定必須保留 REFERENCE，且 invoke 成功」。

S3 Files 這案也適合往後走，因為文章主軸明確指向「讓 S3 bucket 可被當作 file system 存取」。Skill 1 能抽出 S3 Files file system、mount target、S3 bucket、EC2 client、雙向讀寫驗證這些後續可檢查的構件。

## 停止案例怎麼說

Quick Suite 的來源雖然是 AWS 官方新聞，但大多是在描述 agentic teammate、回答問題、採取行動、提升工作效率。Skill 1 可以記錄這些產品主張，但如果文章沒有給出可部署 API、最小架構、權限需求或可重現 recipe，後面就不能把它包裝成「已經知道怎麼 PoC」。

這就是 Skill 1 的價值：先把「可實作證據」和「產品宣稱」分開，讓後面每一步都有可追溯的根據。

## 投影片可放的重點

| 主管會關心的問題 | Skill 1 給的答案 |
|---|---|
| 這篇新聞到底在說什麼？ | 用人看得懂的中文拆成技術變更、使用方式、前提條件與可能價值。 |
| AI 有沒有亂補？ | 報告會標示哪些是 AWS 明講，哪些只是推論或待確認。 |
| 為什麼後面能自動評估？ | 因為 Skill 1 把來源整理成固定欄位，Skill 2 到 Skill 5 都沿用同一條證據線。 |
