---
name: pick-experiment-tracker
description: 追蹤 Cathay AI vs 人類判斷比較實驗（RQ1 成功率、RQ2 效率倍率）——記錄每日「人選 1」的決策、產生統計分析、輸出實驗報告。當使用者說「今天我選 A03」、「記錄我的選擇」、「跑一次盲測」、「本週實驗結果」、「AI vs 人類統計」、「效率倍率是多少」時使用。此 skill 內建了盲測與 AI 輔助兩種模式的分離設計，避免混淆兩種資料——這是實驗方法論的核心，主管會看的。
---

# AI vs 人類判斷實驗追蹤

## 這是什麼

Cathay 內訓專案的三大研究問題（RQ）：
- **RQ1**：AI 系統的判斷成功率是否超過人類？
- **RQ2**：AI 與人類處理時間的效率倍率為何？
- **RQ3**：全自動化是否可行？

本 skill 是 RQ1 與 RQ2 的資料收集器。**關鍵方法論設計**：分離「AI 輔助人類決策」和「盲測」兩種資料，前者只能量測「AI 輔助工作流的效果」，只有後者能量測「AI vs 人類的獨立能力比較」。

## 何時觸發

- 使用者做完決策要記錄（「我選 A03」、「今天選 R-3604DC41」）
- 使用者要跑盲測（「盲測模式」、「先讓我自己選」）
- 使用者要看實驗統計（「本週統計」、「效率倍率」、「AI 命中率」）
- 使用者要輸出實驗報告

## 兩種資料模式

### 模式 A：AI 輔助（assisted，日常營運）
- 每天讀 tech-intel-scan 產出的日報 → 看 AI 選 3 → 從中選 1
- 記錄：AI 的 Top-3、人選、人花時間
- 這種資料**不能**用來回答 RQ1，只能量測「AI 輔助的工作流」

### 模式 B：盲測（blind，每週 2 天）
- 人**先**獨立看 Top-6 選 1 → 再看 AI 選 3
- 記錄：人的獨立選擇、AI 的 Top-3、是否命中、兩者時間
- 這才是 RQ1 有效資料

**警告**：混合兩種模式的資料會讓分析失去意義。此 skill 強制在儲存時打 `mode` 標籤，統計時分開計算。

## 工作流程

### 記錄一筆決策

```bash
# AI 輔助模式（看過 AI 結果後選）
python scripts/record_pick.py --pick A03 --minutes 3

# 盲測模式（先自己選、還沒看 AI）
python scripts/record_pick.py --blind --pick A09 --minutes 15

# 盲測模式下，記錄後 skill 才會把 AI 結果給人看
```

### 查看本週統計

```bash
python scripts/analyze_experiment.py --since "2026-07-06" --until "2026-07-13"
```

輸出：
- 資料筆數（assisted / blind 分開）
- 盲測命中率：人選是否在 AI Top-3 中（RQ1 資料）
- 平均花費時間對比（RQ2 資料）
- **明確的統計 caveats**：n 值多少、信賴區間為何、樣本足夠與否

### 輸出實驗報告

```bash
python scripts/analyze_experiment.py --since ... --output report.html
```

## 誠實聲明模板

實驗報告一定要包含這段，主管會看：

> **統計限制聲明**：本次分析基於 n={盲測筆數} 筆盲測資料。這個樣本數在 95% 信賴區間下的誤差為 ±{margin}%，尚不足以做強結論。效率倍率的計算已包含人工複核時間與系統維護時間，非僅 AI 推論的 wall-clock 時間——避免高估。

## 資料儲存

`data/picks_log.csv`，欄位：

| timestamp | mode | human_pick | ai_top3 | hit_ai_top3 | human_minutes | ai_minutes |
|---|---|---|---|---|---|---|
| 2026-07-13T09:00 | assisted | A03 | A03\|A01\|A06 | True | 3.0 | 0.5 |
| 2026-07-15T09:00 | blind | A09 | A03\|A01\|A06 | False | 15.0 | 0.5 |

`mode` 欄位是**神聖不可混用的**——分析時一定要 `groupby(mode)` 分開算。

## 相關 skill

- `tech-intel-scan`：產生每日 Top-3、每次執行提供 AI 花時間
- `case-study-registry`：無直接關聯，但案例庫品質會間接影響 AI 決策品質，長期實驗要追蹤
