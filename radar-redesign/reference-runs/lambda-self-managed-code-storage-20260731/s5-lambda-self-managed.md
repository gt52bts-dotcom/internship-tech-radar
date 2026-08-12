# Skill 5 PoC 結案報告：AWS Lambda 宣布自主管理程式碼儲存空間 - AWS

## 一眼看重點

- 結論：本次受控 PoC 已完成、已人工確認，並已清除資源。
- 做完發現：Lambda 可以直接參照自管 S3 code package，且建立後仍可正常執行。
- 對公司的意義：這代表大量 Lambda 部署包可以改由自管 S3 bucket 當來源，可能改善部署與儲存治理；下一步要看 rollback、權限和生命週期管理是否可靠。
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
- 用固定評分準則完成 Skill 3 評估，分數為 4.15 / 5。
- 用公開價格建立小型 PoC 成本估算：預期約 USD 0.000249，核准上限 USD 0.05。
- 在 ap-southeast-1 建立受控 PoC 環境。
- 跑完核心驗證：CloudFormation 可以建立使用 REFERENCE 模式的 Lambda；Lambda 建立後可以成功 invoke。
- 完成 AWS Console 人工確認。
- 完成受控清除，避免測試資源繼續產生成本。

## 這次 PoC 證明了什麼

- CloudFormation 可以建立使用 REFERENCE 模式的 Lambda
- Lambda 建立後可以成功 invoke

## 成本與清除狀態

- 預估成本：預期約 USD 0.000249，核准上限 USD 0.05
- 成本性質：這是部署前用公開價格估算，不是 AWS 帳單。
- 清除狀態：已清除並回查。
- 價格來源：AWS 官方公開定價頁。

## 還不能拿來宣稱的事

- 這不是正式生產環境驗證，不能宣稱可直接導入公司正式系統。
- 這次只證明最小 PoC 路徑可行，尚未測效能、可靠性、長時間運作或多人使用。
- 尚未證明 S3 object version rollback、source object 被刪除或撤權時的失敗行為。
- 預估成本不是 AWS 帳單，不能拿來宣稱實際花費。

## 下一步要補的決策證據

- 補 rollback 測試：同一個 Lambda 從不同 S3 object version 切回舊部署包。
- 外部查 REFERENCE 模式下的 bucket policy、code signing、生命週期刪除與 CI/CD 更新模式。

## 官方來源

- https://aws.amazon.com/tw/about-aws/whats-new/2026/07/lambda-self-managed-code-storage/
