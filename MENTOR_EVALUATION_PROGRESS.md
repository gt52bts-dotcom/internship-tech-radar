# 主管評分表自評追蹤

更新日期：2026-07-21  
用途：依實習主管評分表項目，從每日工作日誌、AI PM inbox、Git 產出與驗證證據中追蹤可支持的自評依據。正式成績仍以主管評分為準；若使用者要求，可另列「AI 模擬 mentor 評分」作為表單準備。

Notion 入口：`Cleo｜主管評分自評儀表板`  
https://app.notion.com/p/3a49d9fba316816c8f95d2a2ff997350

Notion 細則頁：`Cleo｜主管評分表細則與回覆`  
https://app.notion.com/p/3a49d9fba316814e923ad82718952a71

GitHub 評分表集合：`evaluation-forms/README.md`

## 計分口徑

- `5`：已有多次可檢查證據，且成果品質、主動性或影響力明確超出基本要求。
- `4`：已有穩定證據，能支持「表現良好」，但仍有公司環境驗證、跨團隊互動或主管回饋不足等限制。
- `3`：有部分證據，但成果仍偏初步、零散或待確認。
- `2`：只有少量跡象，尚不足以支持穩定表現。
- `1`：目前沒有足夠證據，或表現明顯未達期待。

> 截圖解析度有限，下列表述保留主管表單原意；若之後拿到清晰 PDF 或原始表單，需再校正文案。

## 四大評分項目

| 項目 | 目前自評 | 判斷依據 | 補強方向 |
|---|---:|---|---|
| 組織認同／組織承諾 | 4 | 能依 mentor 方向調整專案主線，完成部會自我介紹與雙週誌，並把 Git／Notion／dashboard 作為公司相容的交付紀錄。 | 補更多部門活動、主管回饋或跨部門互動證據。 |
| 盡責 | 5 | 7/16 手動 Step Functions、7/17 CloudFormation、7/20 S3 Files 評估都留下可回驗證據；遇到 AWS 權限、handler、API key、S3 路徑等問題有持續排查與收斂。 | 維持「未驗證不宣稱」與清楚 next step。 |
| 團隊合作 | 4 | 依 mentor 討論修正方向，能把使用者／主管需求轉成 checkpoint、文件、demo checklist 與回報語言。 | 目前跨同事或跨團隊協作證據較少，後續可記錄會議回饋與協作交付。 |
| 創新求變 | 5 | 建立 AI PM、Skill 積分、Evidence Ledger、Human Review Gate、Decision Layer、evaluation harness、互動儀表板等方法，能把 AI 工具整合進可驗證工作流程。 | 補公司環境或主管實際採用後的成效證據。 |

四大項目目前平均：`4.5 / 5`

## Mentor實習生狀況觀察表（15項）

使用者要求改成「假設 AI 是 mentor 來評分」。因此本表新增 AI 模擬 mentor 評分，作為表單準備與補強提醒；正式分數仍以 mentor 最後填寫為準。

AI 模擬 mentor 目前平均：`4.40 / 5`（66 / 15）

完整逐項評分與補強方向：`evaluation-forms/cathay-mentor-observation-form.md`

## 目前建議填表分數

- 四大項目目前平均：`4.5 / 5`。這只適用於上方四大項目自評。
- Mentor 15 項行為觀察：AI 模擬 mentor 平均 `4.40 / 5`；正式分數仍以 mentor 最終評分為準。
- 若表單只能填整數：四大項目可保守以 `4 / 5` 為底，有明確主管口頭佐證時再爭取 `5 / 5`。
- 最需要補強的不是技術能力，而是「跨團隊合作、主管實際滿意度、公司採用後效果」這三類正式外部證據。

## 第二張表單：實習生表現評核

| 表單項目 | 建議評等 | 優點摘要 | 可改善處 |
|---|---|---|---|
| 積極自發、持續學習 | 優異 | 能主動發現問題、查證資料、排查 AWS／CLI／部署問題，並把結果整理成可驗證成果。 | 將探索成果更快對應到主管期待或部門需求。 |
| 團隊合作 | 良好 | 能依 mentor 回饋調整方向，整理主管可讀材料並協助同步資訊。 | 補更多跨同事或跨團隊協作證據。 |
| 創新求變 | 優異 | 將 AI PM、Skill 積分、Evidence Ledger、Human Review Gate、Decision Layer 與 evaluation harness 整合成可追蹤流程。 | 補公司環境實際採用後的成效證據。 |
| 組織認同 | 認同 | 遵守 Git／Notion 同步、17:00 日誌統整、密鑰不入檔與 private repository 等規範。 | 補更多部門活動參與與公司文化連結證據。 |
| 誠信正直 | 是 | 持續區分已驗證、待驗證與估算結果；不記錄或提交 API key、AWS credentials、secret value。 | 持續在對外報告與 final proposal 保留驗證狀態標籤。 |

可直接貼入第二張表單的完整文字整理於 `dashboard/mentor-evaluation-details.md`。
Notion 版細則頁同步保存在 `Cleo｜主管評分表細則與回覆`。

自 2026-07-21 起，評分表資料改集中管理於 `evaluation-forms/`：

- `evaluation-forms/cathay-intern-evaluation-form.md`：國泰｜實習生評鑑表單
- `evaluation-forms/cathay-mentor-observation-form.md`：國泰｜Mentor實習生狀況觀察表
- `evaluation-forms/ntou-internship-effectiveness-questionnaire.md`：學校｜學生校外實習成效問卷（實習機構）
- `evaluation-forms/ntou-internship-performance-evaluation.md`：學校｜學生校外實習成績考核表（實習機構主管用）

## 可引用證據

- `SKILL_PROGRESS.md`：截至 2026-07-20，五個 Skill 累積 91 分。
- `logs/daily/work-log-2026-07-16.md`：公司帳戶手動 Step Functions 全流程跑通。
- `logs/daily/work-log-2026-07-17.md`：CloudFormation 部署與 `company-cfn-001` 成功。
- `logs/daily/work-log-2026-07-20.md`：S3 Files 新聞截斷測試、CLI 查證、CloudFormation template validation。
- `final-proposal/7-17成果素材.md`、`final-proposal/demo-checklist.md`：final proposal 與 demo 證據。
- `dashboard/README.md`、`dashboard/skill-score-data.json`：可攜式 Skill 分數儀表板。
- `dashboard/mentor-evaluation-details.md`：主管可讀的評分細則與第二張表單回覆。
- `evaluation-forms/README.md`：評分表集合入口。
- Notion `Cleo｜主管評分自評儀表板`：主管評分表自評入口與每日更新規則。
- Notion `Cleo｜主管評分表細則與回覆`：第二張表單評分、優點／可改善處與綜合回饋。
