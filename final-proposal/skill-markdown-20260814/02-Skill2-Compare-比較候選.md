# Skill 2 Compare｜把多篇新聞排成可討論的候選清單

## 一句話定位

Skill 2 是「候選分流」。它把 Skill 1 掃到的新技術放在同一張比較表裡，先看哪個值得深入評估、哪個需要補資料、哪個雖然熱門但不適合現在做 PoC。

## 比較表應該長這樣

| 比較欄位 | Lambda self-managed code storage | S3 Files | WorkSpaces AI Agents | Quick Suite |
|---|---|---|---|---|
| 技術變更是否明確 | 明確：Lambda 直接參照 S3 package。 | 明確：S3 bucket 可透過 file system 型態存取。 | 中等：AI agent 操作 desktop app，但完整互動範圍較重。 | 偏弱：多為產品能力與效益描述。 |
| 最小 PoC 是否可定義 | 可：S3 bucket + Lambda + REFERENCE 設定 + invoke。 | 可：S3 Files + mount target + EC2 mount + S3 雙向讀寫。 | 可做 phase 1 infrastructure，但完整 agent session 成本與合規風險較高。 | 不清楚：缺少可直接部署的最小 recipe。 |
| 成本可預估性 | 高：Lambda request、duration、S3 storage 都有明確計價單位。 | 中高：可估 EC2、S3 Files、S3、網路與短時段成本。 | 中低：一開 session 可能牽涉月費型 Windows/RDS SAL。 | 低：沒有最小資源清單就無法嚴謹報價。 |
| 驗證問題 | REFERENCE 設定是否真的保留？函數能否正常 invoke？ | S3 到 mount、mount 到 S3 是否真的雙向同步？ | 不開完整 session 時，phase 1 能證明多少價值？ | 若沒有 API / recipe，PoC 到底要證明什麼？ |
| 初步方向 | 進 Skill 3，並可進 Skill 4。 | 進 Skill 3，並可進 Skill 4。 | 進 Skill 3，但需嚴格切 phase 和成本。 | 進 Skill 3 後多半停止。 |

## Skill 2 的判斷準則

| 準則 | 觀察重點 | 影響 |
|---|---|---|
| 企業關聯度 | 是否能連到公司雲端治理、開發流程、資料存取、成本控管或營運效率。 | 決定要不要花時間進 Skill 3。 |
| 可驗證性 | 是否能在 sandbox 中用小資源驗證一個明確命題。 | 可驗證性高，才適合 PoC。 |
| 成本透明度 | 是否能在 Skill 3 前用官方價格單位估出低/中/高情境。 | 成本不透明會拉高停止風險。 |
| 權限與清除範圍 | 是否能先列出會碰哪些服務、IAM action、cleanup 方法。 | 影響能不能安全進 Skill 4。 |
| 決策增量 | PoC 成功後是否會讓主管多知道一件可決策的事。 | 如果只是 demo 產品聲量，就不值得硬做。 |

## 和人工手動比較的亮點

人工看 AWS 新聞時，很容易被「新、熱門、看起來厲害」吸引。Skill 2 的作用是把不同候選放到同一張尺上，比較實作路徑、成本邊界、驗證問題和停止條件是否清楚。

例如 Lambda 和 S3 Files 不是因為分數看起來高才成功，而是因為 Skill 2 已經能看出它們都有明確的最小驗證問題。WorkSpaces 和 Quick Suite 的價值不一定低，但一個牽涉 session / 月費 / 合規邊界，一個缺少實作細節，所以不應被推進成同樣規格的 live PoC。

## 投影片可放的重點

| 主管會關心的問題 | Skill 2 給的答案 |
|---|---|
| 為什麼選 Lambda 和 S3 Files？ | 因為它們不只新，而且有可部署、可驗證、可清除的最小實驗。 |
| 為什麼不選看起來很 AI 的服務？ | 因為 PoC 要有決策增量；若成本、合規或 recipe 不清，就先停。 |
| AI 在這關的價值是什麼？ | 它把候選拉到同一張比較表，避免人靠印象挑題目。 |
