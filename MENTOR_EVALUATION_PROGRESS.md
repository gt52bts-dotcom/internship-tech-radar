# 主管評分表自評追蹤

更新日期：2026-08-17  
用途：依實習主管評分表項目，從每日工作日誌、AI PM inbox、Git 產出與驗證證據中追蹤可支持的自評依據。正式成績仍以主管評分為準；若使用者要求，可另列「AI 模擬 mentor 評分」作為表單準備。

Notion 入口：`Cleo｜主管評分自評儀表板`  
https://app.notion.com/p/3a49d9fba316816c8f95d2a2ff997350

Notion 細則頁：`Cleo｜主管評分表細則與回覆`  
https://app.notion.com/p/3a49d9fba316814e923ad82718952a71

GitHub 評分表集合：`evaluation-forms/README.md`

## 計分口徑

- `5`：已有多次可檢查證據，且成果品質、主動性或影響力明確超出基本要求。
- `4`：已有穩定證據，能支持「表現良好」，但仍有公司環境驗證、主管回饋或正式採用成效不足等限制。
- `3`：有部分證據，但成果仍偏初步、零散或待確認。
- `2`：只有少量跡象，尚不足以支持穩定表現。
- `1`：目前沒有足夠證據，或表現明顯未達期待。

> 截圖解析度有限，下列表述保留主管表單原意；若之後拿到清晰 PDF 或原始表單，需再校正文案。

## 四大評分項目

| 項目 | 目前自評 | 判斷依據 | 補強方向 |
|---|---:|---|---|
| 組織認同／組織承諾 | 5 | 完成 8/14 `預言者雷達`成果分享與 CIP 雙週誌，能配合公司相容的 Git／Notion／README 紀錄、敏感資訊不入檔、成本／授權 gate 與公司環境限制不外推；協理回饋也指出後續可朝公司內部環境與同仁帳號使用延伸。 | 補正式書面主管回饋、公司內部環境導入條件或 8/20 後續活動紀錄。 |
| 盡責 | 5 | 長期留下可回查證據；8/13-8/14 Lambda 與 S3 Files PoC cleanup 已回查，且誠實標示 `closed_without_console_review`，不把未完成 Console review 的結果寫成正常 final。 | 維持「未驗證不宣稱」，下一步補服務化提案與可重現啟動方式。 |
| 團隊合作 | 4.5 | 除 mentor 對齊、主動回報、文件同步與依回饋調整方向外，已參與共融活動與實習生交流，並能把協理／mentor-skill 回饋分清楚放入對應專案。因單位只有一個實習職缺，正式跨團隊共同交付證據仍較少。 | 若表單只能填整數，建議填 `4` 或對應 `優異`；後續補正式會議互動、主管交辦協調或跨單位同步證據。 |
| 創新求變 | 5 | 建立 `預言者雷達`五個 Skill、受控 PoC、Evidence Ledger、Human Review Gate、成本估算、cleanup 規則、AI PM、Skill 積分與 dashboard；協理回饋肯定此方向不同於一般 GPT 零散提問，且有內部推廣潛力。 | 補公司內部環境落地、一次分析成本與可量化效益。 |

四大項目目前平均：`4.875 / 5`

## Mentor實習生狀況觀察表（15項）

使用者要求改成「假設 AI 是 mentor 來評分」。因此本表新增 AI 模擬 mentor 評分，作為表單準備與補強提醒；正式分數仍以 mentor 最後填寫為準。

AI 模擬 mentor 目前平均：`4.87 / 5`（73 / 75）

完整逐項評分與補強方向：`evaluation-forms/cathay-mentor-observation-form.md`

## 目前建議填表分數

- 四大項目目前平均：`4.875 / 5`。這只適用於上方四大項目自評。
- Mentor 15 項行為觀察：AI 模擬 mentor 平均 `4.87 / 5`；正式分數仍以 mentor 最終評分為準。
- 若表單只能填整數：組織認同、盡責、創新求變可爭取 `5 / 5`；團隊合作建議保守填 `4 / 5` 或對應 `優異`，除非主管願意把 mentor 對齊與文件同步視為主要團隊合作證據。
- 最需要補強的不是技術能力，而是「正式書面主管回饋、公司內部環境落地條件、一次分析成本與可量化效益」這三類外部證據。

## 第二張表單：實習生表現評核

| 表單項目 | 建議評等 | 優點摘要 | 可改善處 |
|---|---|---|---|
| 積極自發、持續學習 | 傑出 | 主動把模糊 AI 技術雷達題目拆成五個 Skill，完成案例、PoC、成果發表與服務化缺口整理。 | 將下一步服務化提案補上成本效益與內部環境條件。 |
| 團隊合作 | 優異 | 能依 mentor／主管回饋調整方向，主動回報限制，並把不同來源回饋放入正確證據邊界；也有實習生活動交流。 | 補正式跨同事共同交付或主管交辦協調案例。 |
| 創新求變 | 傑出 | 將 AI 技術雷達做成五個 Skill、受控 PoC 與證據治理流程，並建立 AI PM 與 dashboard 追蹤機制。 | 補公司環境實際採用後的量化成效。 |
| 組織認同 | 非常認同 | 遵守 Git／Notion 同步、17:00 日誌統整、密鑰不入檔、授權與成本 gate，並把成果下一步連到公司內部環境。 | 補正式公司端導入條件或主管書面回饋。 |
| 誠信正直 | 是 | 持續區分已驗證、使用者回報、mentor 觀點、協理回饋、估算與待公司環境驗證；不提交敏感資訊。 | 持續在對外報告保留驗證狀態標籤。 |

可直接貼入第二張表單的完整文字整理於 `dashboard/mentor-evaluation-details.md`。
Notion 版細則頁同步保存在 `Cleo｜主管評分表細則與回覆`。

自 2026-07-21 起，評分表資料改集中管理於 `evaluation-forms/`：

- `evaluation-forms/cathay-intern-evaluation-form.md`：國泰｜實習生評鑑表單
- `evaluation-forms/cathay-mentor-observation-form.md`：國泰｜Mentor實習生狀況觀察表
- `evaluation-forms/ntou-internship-effectiveness-questionnaire.md`：學校｜學生校外實習成效問卷（實習機構）
- `evaluation-forms/ntou-internship-performance-evaluation.md`：學校｜學生校外實習成績考核表（實習機構主管用）

## 可引用證據

- `SKILL_PROGRESS.md`：截至 2026-08-14，五個 Skill 累積 178 分（每日總分最高 10 分的新口徑）。
- `logs/daily/work-log-2026-07-16.md`：公司帳戶手動 Step Functions 全流程跑通。
- `logs/daily/work-log-2026-07-17.md`：CloudFormation 部署與 `company-cfn-001` 成功。
- `logs/daily/work-log-2026-08-14.md`：成果發表、雙週誌交出、Lambda / S3 Files cleanup 回查與限制標示。
- `AI_PM_INBOX.md`：8/17 協理回饋、mentor-skill 評價與 8/19 AI PM 草稿整理。
- `final-proposal/2026-08-19-AI-PM科會分享-Markdown草稿.md`：AI PM 分享文字草稿與證據邊界示範。
- `dashboard/README.md`、`dashboard/skill-score-data.json`：可攜式 Skill 分數儀表板。
- `dashboard/mentor-evaluation-details.md`：主管可讀的評分細則與第二張表單回覆。
- `evaluation-forms/README.md`：評分表集合入口。
- Notion `Cleo｜主管評分自評儀表板`：主管評分表自評入口與每日更新規則。
- Notion `Cleo｜主管評分表細則與回覆`：第二張表單評分、優點／可改善處與綜合回饋。
