# 技術雷達 Skill 積分紀錄

## Skill 定義

- `Skill 1 - Scan`：蒐集 AWS 新聞、官方文件、候選技術與問題線索。
- `Skill 2 - Compare`：比較候選技術、替代方案、限制、成本與適用情境。
- `Skill 3 - Evaluate`：用 rubric、風險、權限、安全、成本與可行性做決策。
- `Skill 4 - Validate`：以 CLI、CloudFormation、測試、PoC 或證據包驗證推論。
- `Skill 5 - Report`：產出可交付報告、dashboard、demo checklist、日誌與主管可讀材料。

## 評分標準

- `+1`：只有閱讀、整理或小幅修正，缺乏明確驗證。
- `+2~3`：有可追溯文件、指令查證、候選比較或局部 PoC。
- `+4~5`：完成具體設計、可行性評估、報告或中等規模驗證。
- `+6~7`：完成端到端 PoC、可重建驗證與清楚證據鏈。
- `+8~10`：接近公司環境正式驗證，含監控、回歸、成本、安全與完整 cleanup 回驗。

## 每日分數

| 日期 | Scan | Compare | Evaluate | Validate | Report | 當日總分 | 目標對齊 |
|---|---:|---:|---:|---:|---:|---:|---|
| 2026-07-13 | 3 | 3 | 3 | 5 | 3 | 17 | direct |
| 2026-07-14 | 2 | 2 | 2 | 2 | 2 | 10 | supporting |
| 2026-07-15 | 1 | 1 | 1 | 2 | 3 | 8 | supporting |
| 2026-07-16 | 2 | 2 | 4 | 6 | 4 | 18 | direct |
| 2026-07-17 | 3 | 4 | 6 | 7 | 4 | 24 | direct |
| 2026-07-20 | 3 | 2 | 3 | 4 | 2 | 14 | direct |
| 2026-07-21 | 2 | 2 | 3 | 6 | 3 | 16 | direct |
| **累積** | **16** | **16** | **22** | **32** | **21** | **107** |  |

## 2026-07-21 評分理由

- Scan +2：聚焦 S3 Files AWS News、官方文件、CLI schema 與使用條件；但只處理單一新聞與單一服務，不算廣泛掃描。
- Compare +2：比較 CLI direct resource 與 CloudFormation-managed resource、direct mount 與 access point mount；但未進一步比較多個替代服務。
- Evaluate +3：納入 IAM、POSIX 權限、成本、cleanup、去識別化證據與 exposed private key 風險；但缺完整成本估算與正式採用決策。
- Validate +6：手動 CLI PoC 與 CloudFormation-managed PoC 都完成實機雙向驗證；但未做效能、多節點、長時間穩定性與 cleanup 後回驗。
- Report +3：產出教學書、流程圖、證據摘錄、雷達式 PoC 報告與正式日誌；尚未濃縮成 final proposal 或主管版結論頁。

## 當前狀態

截至 2026-07-21，累積總分為 107。Skill 4 仍是最高，代表專案已從文件設計推進到多次可驗證 PoC；下一步要補強的是 cleanup 回驗、automation 準時性、成本估算，以及把新聞重點抽取能力寫成可展示案例。
