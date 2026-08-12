# Skill 4 Validate｜只在核准後建立受控 AWS PoC

## 一句話定位

Skill 4 是唯一會建立 AWS 資源、可能產生成本的階段。它不是自動部署展示，而是在 Skill 3 放行、具名核准和成本上限成立後，用最小 PoC 補上決策證據。

## 人類應該怎麼理解

Skill 4 的價值不是「AI 會開資源」。真正有價值的是：它只在該做的時候開資源，只開證明問題需要的資源，驗證完留下 runtime、資源盤點、權限面和 cleanup 回查。

也就是說，Skill 4 不追求把 demo 做漂亮，而是回答 Skill 3 無法完全回答的問題：在這個帳號和 Region 裡，真的部署得起來嗎？服務之間接得起來嗎？驗證通得過嗎？最後收得乾淨嗎？

## 它實際做什麼

- 先產出 approval gate；沒有核准時只會停在等待，不會偷偷部署。
- 檢查 Skill 3 是否建議 PoC、是否有完整報價、是否有可部署 recipe。
- 要求人類具名核准、核准成本上限、`deployment_authorized=true` 和明確 `--execute`。
- 使用已登錄 recipe 建立受控 AWS sandbox 資源。
- 驗證 runtime 行為，例如 Lambda invoke、S3 Files 雙向同步。
- 產出 resource inventory，列出實際資源、報價是否涵蓋、IAM 權限面與 resource status。
- cleanup 前留下即時用量快照，cleanup 後回查資源是否已清除。

## 亮點

- **預算在前，部署在後**：成本上限和人類核准必須先成立，不是 PoC 完成後才進報告。
- **recipe registry 防止臨場硬做**：沒有可部署 recipe，就算技術值得看，也不能直接建 AWS 資源。
- **resource inventory 取代只看截圖**：截圖可以輔助，但真正可審查的是結構化資源盤點。
- **run-scoped cleanup**：只清這次 run 建立的資源，不做大範圍刪除。
- **把成功定義成證據**：部署完成、runtime 通過、權限面可查、cleanup 可回查，才算有決策價值。

## 案例中可以怎麼講

- Lambda：驗證 CloudFormation 能建立 Amazon S3 reference code storage，Lambda invoke 成功。
- S3 Files：驗證 S3 Files、VPC、EC2、mount、SSM、IAM 等資源能串起來，且能做 Amazon S3 到 mount、mount 到 Amazon S3 的雙向驗證。
- WorkSpaces：即使有 phase-1 recipe，也因完整桌面 session 有月費與合規風險，目前不應硬進 live Skill 4。
- Quick Suite：缺少可部署 recipe 與實作細節，因此沒有建立 AWS 資源。
