# 技術雷達 Skill 積分紀錄

## Skill 定義

- `Skill 1 - Scan`：蒐集 AWS 新聞、官方文件、候選技術與問題線索。
- `Skill 2 - Compare`：比較候選技術、替代方案、限制、成本與適用情境。
- `Skill 3 - Evaluate`：用 rubric、風險、權限、安全、成本與可行性做決策。
- `Skill 4 - Validate`：以 CLI、CloudFormation、測試、PoC 或證據包驗證推論。
- `Skill 5 - Report`：產出可交付報告、dashboard、demo checklist、日誌與主管可讀材料。

## 評分標準

- 五個 Skill 的每日加總最高 10 分，不再用「每個 Skill 各自最高 10 分」累加。
- `1~3`：閱讀、整理、模板驗證、單點 CLI 查證或局部文件成果。
- `3~5`：本機 PoC、離線驗證、可追溯設計或小型可交付成果。
- `6~8`：公司帳戶或接近真實環境的端到端 PoC，但仍有 fallback、未回驗、未 cleanup 或品質限制。
- `9~10`：可重現、可展示、品質已回驗，且對核心目標有明確里程碑意義。若缺正式 API、cleanup、成本、安全或穩定性驗證，不可超過 10，也通常不給滿分。

## 每日分數

| 日期 | Scan | Compare | Evaluate | Validate | Report | 當日總分 | 目標對齊 |
|---|---:|---:|---:|---:|---:|---:|---|
| 2026-07-13 | 1 | 2 | 1 | 3 | 1 | 8 | direct |
| 2026-07-14 | 1 | 1 | 1 | 2 | 1 | 6 | supporting |
| 2026-07-15 | 1 | 1 | 1 | 1 | 1 | 5 | supporting |
| 2026-07-16 | 1 | 1 | 2 | 3 | 1 | 8 | direct |
| 2026-07-17 | 1 | 1 | 2 | 4 | 2 | 10 | direct |
| 2026-07-20 | 2 | 1 | 2 | 1 | 1 | 7 | direct |
| 2026-07-21 | 1 | 1 | 2 | 4 | 1 | 9 | direct |
| 2026-07-22 | 1 | 1 | 2 | 2 | 2 | 8 | direct |
| **累積** | **9** | **9** | **13** | **20** | **10** | **61** |  |

## 2026-07-21 評分理由

- Scan +1：聚焦 S3 Files AWS News、官方文件、CLI schema 與使用條件；但只處理單一新聞與單一服務，不算廣泛掃描。
- Compare +1：比較 CLI direct resource 與 CloudFormation-managed resource、direct mount 與 access point mount；但未進一步比較多個替代服務。
- Evaluate +2：納入 IAM、POSIX 權限、成本、cleanup、去識別化證據與 exposed private key 風險；但缺完整成本估算與正式採用決策。
- Validate +4：手動 CLI PoC 與 CloudFormation-managed PoC 都完成實機雙向驗證；但未做效能、多節點、長時間穩定性與 cleanup 後回驗。
- Report +1：產出教學書、流程圖、證據摘錄、雷達式 PoC 報告與正式日誌；尚未濃縮成 final proposal 或主管版結論頁。

## 當前狀態

截至 2026-07-22，累積總分為 61。Skill 4 仍是最高，代表專案已從文件設計推進到可驗證 PoC，也完成一輪 cleanup 回驗；今天已補上 CloudFormation Infrastructure Composer 資源關係截圖，下一步是由 Cleo 在 Console / EC2 確認 S3 Files mount 與雙向同步，再做 cleanup。這份分數已改採每日總分最高 10 分的新口徑，舊分數不可再作為正式累積值。

## 2026-07-22 評分理由

- Scan +1：盤點 S3 bucket、CloudTrail 與 S3 Files 相關資源，辨識哪些是專案資源、哪些是帳號治理資源；掃描範圍仍集中在 S3 Files cleanup 與帳號資源。
- Compare +1：比較手動 CLI、CDK deploy、CloudFormation deploy、Session Manager 與 SSH 的差異，並寫入教學書；尚未比較 S3 Files 與其他替代儲存服務。
- Evaluate +2：把成本、cleanup、CloudTrail 稽核、CDK bootstrap 權限限制、S3 prefix 路徑與日誌誠實度納入判斷；但新 stack 仍待 cleanup。
- Validate +2：完成舊 PoC cleanup 回驗，用 CLI 確認新 CloudFormation stack `CREATE_COMPLETE`，並由使用者截圖確認 Infrastructure Composer 資源關係；但尚未完成 EC2 mount 檢查與 S3 雙向同步驗證。
- Report +2：重寫日誌規則與歷史日誌，完成 CDK 部署教學書、CloudFormation 註解整理與 dashboard 同步；但 final proposal 仍待整理。
