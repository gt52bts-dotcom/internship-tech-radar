# 2026-08-04｜Skill 1 雷達新功能候選文章

本次依 Skill 1 discovery 掃描 AWS 官方來源，條件為一年內、具官方 GA 證據、排除 Bedrock、目標區域為 `ap-southeast-1`。本輪只做到 Skill 1 / Skill 2 候選整理，尚未進入 Skill 3 評估、報價或 PoC。

原始 artifacts：

- `radar-redesign/out/s1-radar-20260804-new-features/s1.json`
- `radar-redesign/out/s1-radar-20260804-new-features/s2.json`

## 最值得優先評估

| 優先度 | 候選 | 為什麼適合實作 | 進 Skill 3 前要注意 |
|---|---|---|---|
| 1 | Announcing General Availability of DynamoDB Mapper for Kotlin | 可用小型 Kotlin 程式搭配 DynamoDB table 驗證讀寫、查詢、資料型別 mapping；PoC 範圍小，成功條件清楚。 | 目前 S2 未確認 `ap-southeast-1` 功能級 Region 證據與正式 PoC 報價；需要 Skill 3 補報價與 proof question。 |
| 2 | Amazon EC2 C9g and C9gd instances powered by AWS Graviton5 processors are now available | 可用小型 EC2 benchmark 驗證 instance family 是否可部署、基本效能與啟停 cleanup；PoC 證據直接。 | 可能產生較明確 EC2 成本；目前 S2 有 pricing evidence，但缺新加坡功能級 Region 證據。 |
| 3 | AWS SDK for SAP ABAP Knowledge MCP Server | 可做文件 / MCP / IDE 輔助型 PoC，成本可能低，不一定需要建立大量 AWS 資源。 | 需要 SAP ABAP 或替代 demo context；若沒有合適環境，容易變成文件驗證而非 Skill 4 PoC。 |

## 可評估但 PoC 較重

| 候選 | 適合點 | 主要風險 |
|---|---|---|
| Amazon WorkSpaces Now Lets AI Agents Operate Desktop Applications | 題目很貼近 AI agent 操作桌面應用，主管可能容易理解應用價值。 | WorkSpaces 環境與授權較重，部署成本與帳號權限可能比前兩項高。 |
| AWS Transform continuous modernization / technical debt remediation | 題目與 AI 自動化維運、技術債分析有關，概念有展示價值。 | AWS Transform 類服務常涉及連 GitHub/GitLab/Bitbucket workspace，可能牽涉權限與真實 repo；小型可控 PoC 不一定容易。 |
| AWS Transform Agent Builder Toolkit | 可討論客製 agent workflow 與 reusable agent。 | 可能需要 AWS Transform / Kiro / agent toolkit 相關環境，PoC recipe 尚未存在。 |

## 不建議作為下一個 Skill 4 PoC

| 候選 | 原因 |
|---|---|
| Now Open—AWS Local Zones in Athens, Greece | 是區域基礎設施開放，不適合作為 `ap-southeast-1` 小型 PoC；更像地理可用性新聞。 |

## 建議下一步

優先拿 `DynamoDB Mapper for Kotlin` 進 Skill 3。這題最適合回答新的 PoC proof question：

- 這次 PoC 要證明什麼：Kotlin 應用是否能用 DynamoDB Mapper 完成基本 table mapping、put/get/query，並比低階 API 更容易寫出可讀程式。
- 如果成功，決策者會多知道什麼：這個新功能不只是官方 GA，而是能在小型程式中實際完成資料模型對應與 DynamoDB 操作。
- 仍未知什麼：真實公司專案是否使用 Kotlin、複雜 schema / transaction / production IAM 設計是否適合，仍需後續評估。

第二順位可選 `EC2 C9g/C9gd Graviton5`，但它比較像效能與成本測試，PoC 成本與 benchmark 設計要先講清楚。
