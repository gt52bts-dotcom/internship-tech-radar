# Work Log Formats

## Daily Log

Notion database properties:

- `名稱`: date only in `M/D` format, for example `7/13`.
- `副標題`: one concise summary of the day's most important outcome.
- `日期`: the full date used for filtering and sorting.
- `Mentor 討論關鍵字`: searchable notes that remain hidden from gallery cards.

Do not include project names or progress descriptions in `名稱`; place them in `副標題`.

```markdown
# 工作日誌 - YYYY-MM-DD

## 今日結論

一句話說明今天最重要的進展與目前狀態。

## 完成事項

- 完成什麼，產出什麼，影響是什麼。

## 技術決策

- 決策：
- 原因：
- 替代方案：
- 風險：

## 產出檔案與證據

- `path/to/file`：用途或內容。

## 測試與驗證

- 指令：
- 結果：
- 未驗證項目：

## 遇到問題與處理

- 問題：
- 原因：
- 處理：
- 尚待確認：

## 明日計畫

- 下一步。

## 需要主管協助或確認

- 需要確認的權限、方向、資源或評分標準。
```

## Weekly Summary

```markdown
# 週報 - YYYY-MM-DD 至 YYYY-MM-DD

## 本週總結

## 主要完成

## 架構與技術決策

## Demo / 交付狀態

## 風險與阻塞

## 下週計畫

## 需要主管確認
```

## Biweekly Summary

The biweekly report is a synthesis, not a diary. Group details by meaning and retain only evidence that supports the conclusion.

```markdown
# 雙週誌 - YYYY-MM-DD 至 YYYY-MM-DD

## 本期一句話總結

用一句話交代這兩週最重要的成果、價值與目前狀態。

## 核心成果與影響

- 成果：完成了什麼可交付內容。
  - 影響：對專案、團隊或後續工作的幫助。
  - 證據：檔案、Demo、驗證結果或主管回饋。

## 關鍵問題與解法

- 問題與限制：
- 判斷與解法：
- 為什麼這樣做：
- 結果或待驗證事項：

## 學習與能力成長

- 原本：
- 公司提供的支持：專案情境、Mentor 回饋、工具、規範或協作機會。
- 現在能做到：
- 成長證據：

## 下期重點

- 最多三項，寫預期成果，不寫零碎待辦。

## 需要主管協助或確認

- 僅列真正需要決策、權限或資源的事項。
```

## Handoff Note

```markdown
# 交接紀錄 - 專案名稱

## 目前狀態

## 可直接使用的檔案

## 如何執行

## 尚未完成

## 注意事項

## 建議下一步
```
