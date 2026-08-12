# Skill 5 Report｜把前四關證據整理成主管可看的報告

## 一句話定位

Skill 5 不重新發明結論。它只讀 Skill 1 到 Skill 4 已留下的 artifact，把來源、比較、評分、報價、runtime、resource inventory、cleanup 和限制整理成可交付的技術報告。

## 人類應該怎麼理解

PoC 最怕的是「做完了，但沒人知道到底證明了什麼」。Skill 5 的任務是把整條證據鏈說清楚：這個技術從哪篇文章來，前面怎麼判斷，為什麼進或不進 PoC，實作後驗證了什麼，還有哪些不能宣稱。

它讓成果不是一次 demo，而是一份能被主管、mentor 或下一位接手者追問的報告。

## 它實際做什麼

- 檢查 Skill 1 到 Skill 4 artifact 的 `run_id` 和 lineage 是否一致。
- 不重新評分，只呈現 Skill 3 的 score breakdown 和理由。
- 不重新報價，只呈現 Skill 3 的 low / expected / high、公式、來源與成本型態。
- 如果有 Skill 4 runtime，就整理部署狀態、runtime check、resource inventory、權限面、cleanup 結果。
- 把已驗證、已實作但待公司環境驗證、估算或未知限制分開標示。
- 產出 JSON、Markdown 和 GUI model；可作為簡報與交接素材。

## 亮點

- **證據鏈可追溯**：每個結論都能回到 Skill 1 到 Skill 4 的某個 artifact。
- **不過度宣稱**：公開牌價估算不是 AWS 帳單；sandbox PoC 不是公司 production 驗證。
- **成功和停止都能報告**：成功案例走到 final；停止案例也能用 Skill 3 報告說明為何不該硬做。
- **可回答主管追問**：不只寫「成功」，還寫成功證明了什麼、仍不知道什麼、下一步是什麼。
- **保留交接價值**：下一個人不需要翻聊天紀錄，也能從報告知道流程與證據。

## 案例中可以怎麼講

- Lambda 和 S3 Files 走到 Skill 5 final，所以能展示完整證據鏈：來源、評估、報價、部署、驗證、cleanup、限制。
- WorkSpaces 和 Quick Suite 沒有進 Skill 4，但仍有 Skill 3 決策報告；它們證明這套流程不只會做 demo，也會保留停止理由。
- S3 Files 的 Skill 5 特別能展示 resource inventory 和 cleanup 價值，因為它不是一張截圖，而是可回查的資源與權限證據。
