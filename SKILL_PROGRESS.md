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
| 2026-07-21 | 3 | 3 | 5 | 7 | 5 | 23 | direct |
| **累積** | **17** | **17** | **24** | **33** | **23** | **114** |  |

## 2026-07-21 評分理由

- Scan +3：聚焦 S3 Files AWS News、官方文件、CLI schema 與使用條件，屬明確但非廣泛掃描。
- Compare +3：比較 CLI direct resource 與 CloudFormation-managed resource、direct mount 與 access point mount、S3 API 與檔案系統存取。
- Evaluate +5：把 IAM、POSIX 權限、AWS 成本、cleanup、去識別化證據與 exposed private key 風險納入判斷。
- Validate +7：手動 CLI PoC 與 CloudFormation-managed PoC 都完成實機雙向驗證；未做效能、多節點、長時間穩定性與 cleanup 後回驗，因此不給 8 分以上。
- Report +5：產出教學書、流程圖、證據摘錄、雷達式 PoC 報告與正式日誌。

## 當前狀態

截至 2026-07-21，累積總分為 114。Skill 4 仍是最高，代表專案已從文件設計推進到多次可驗證 PoC；下一步要補強的是 cleanup 回驗、automation 準時性與把新聞重點抽取能力寫成可展示案例。
