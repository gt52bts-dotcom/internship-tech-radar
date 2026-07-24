# Cleo 的暑期實習專案（2026 CIP）

本 repository 是 Cathay Tech Intel v3 / 技術雷達實習專案的工作紀錄與交付物中心。Git 是 source of truth；Notion 與 dashboard 用於呈現每日進度與 Skill 成長。

## 主管快速入口

| 按鈕 | 說明 |
|---|---|
| [▶ 查看評分表集合（GitHub）](./evaluation-forms/README.md) | 可選不同評分表：國泰實習生評鑑表單、國泰 Mentor 觀察表、學校成效問卷與成績考核表。 |

## 專案狀態

目前主線已從本地設計與手動 Console 部署，推進到公司 AWS 帳戶可用 CloudFormation 重建並端到端驗證的版本。

```mermaid
flowchart LR
    A["定義技術雷達流程"] --> B["建立 AWS PoC 架構"]
    B --> C["整理手動部署封包"]
    C --> D["公司 AWS 帳戶手動部署"]
    D --> E["CloudFormation 可重建部署"]
    E --> F["Step Functions 端到端驗證"]
    F --> G["治理證據、報告與 final proposal 素材"]
```

## 每日工作日誌

| 日期 | 今日主軸 | 狀態 |
|---|---|---|
| [7/23](./logs/daily/work-log-2026-07-23.md) | 指定 S3 Files 新聞跑完 S1-S5，釐清 LLM fallback 原因並開始整理 AI PM 科會簡報 | direct |
| [7/22](./logs/daily/work-log-2026-07-22.md) | 調嚴日誌與 Skill 分數，清理舊 S3 Files PoC，建立 CDK / CloudFormation 可重做部署流程 | direct |
| [7/21](./logs/daily/work-log-2026-07-21.md) | 完成 S3 Files 手動與 CloudFormation-managed PoC 證據整理，建立評分表框架並同步正式日誌 | direct |
| [7/20](./logs/daily/work-log-2026-07-20.md) | 整理 final proposal 與 demo 材料，完成 S3 Files 新聞截斷測試、CLI 查證與 CloudFormation template validation | direct |
| [7/17](./logs/daily/work-log-2026-07-17.md) | CloudFormation 公司帳戶部署成功，完成 governance artifacts、7 頁簡報與 AI 執行軌跡 | direct |
| [7/16](./logs/daily/work-log-2026-07-16.md) | 公司 AWS 帳戶 Step Functions 全流程跑通，完成 API-first fallback 與 HR 雙週誌格式修正 | direct |
| [7/15](./logs/daily/work-log-2026-07-15.md) | 建立 AI PM、GitHub、Notion、Skill dashboard 與公司帳戶部署準備 | supporting |
| [7/14](./logs/daily/work-log-2026-07-14.md) | 整理 v3 手動部署包與 AWS 部署限制 | supporting |
| [7/13](./logs/daily/work-log-2026-07-13.md) | 建立 v3 技術雷達與 AWS pipeline 設計骨架 | direct |

## 紀錄目錄

- `logs/daily/`：正式每日實習日誌，17:00 後統整。
- `ai-execution-trace/daily/`：AI 每小時執行軌跡，只記錄 AI 當小時的判斷、產出與驗證，不寫專案前情提要。

## Skill 進度

- [Skill 進度完整紀錄](./SKILL_PROGRESS.md)
- [互動儀錶板 README](./dashboard/README.md)
- [可嵌入 dashboard HTML](./dashboard/cleo-skill-dashboard.html)

截至 2026-07-23，改採硬審核口徑後累積分數 66 分。每日五個 Skill 加總最高 10 分，舊版 107 分不再作為正式值。

| Skill | 說明 | 累積分數 |
|---|---|---:|
| Skill 1｜掃描 | 資料來源掃描、候選技術收集、帳號資源盤點 | 10 |
| Skill 2｜比較 | 候選技術比較、部署方式與限制對照 | 10 |
| Skill 3｜評估 | 評分邏輯、風險、成本與可行性判斷 | 14 |
| Skill 4｜驗證 | 部署驗證、權限驗證、錯誤排查 | 21 |
| Skill 5｜報告 | 報告、教學書、dashboard、週誌 | 11 |

## 重要交付物

- [AI PM 工作流程](./AI_PM_WORKFLOW.md)
- [專案記憶](./PROJECT_MEMORY.md)
- [公司如何幫助我成長草稿](./final-proposal/公司如何幫助我成長-草稿.md)
- [簡報架構與執行軌跡](./final-proposal/簡報架構與執行軌跡.md)
- [7/17 AI 執行軌跡](./ai-execution-trace/daily/2026-07-17.md)
- [CloudFormation 手動部署 README](./radar-company-account-complete/radar/manual-cloudformation/README.md)
- [HR 雙週工作週誌格式正確版](./2026CIP_王冠婷_雙週工作週誌1_格式正確版.docx)

## 目前待辦

- 若要驗證真實 LLM 評分，需更新正式 Anthropic API key 或改走公司核准的 Bedrock 路徑。
- 繼續累積 human review logs，讓 `feedback-stats.json` 從少量資料變成可說明趨勢。
- 補有效 API key 重跑、真人 PoC 審查紀錄與 cleanup；既有 PoC 的補證據不列為個人日誌核心成果。
- 將 7/17 CloudFormation 成功、governance artifacts 與報告畫面整理進 final proposal。
- 若要正式使用 7 頁部會自我介紹簡報，可再補 speaker notes 或口說稿。
