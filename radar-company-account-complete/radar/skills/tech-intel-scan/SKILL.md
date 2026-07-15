---
name: tech-intel-scan
description: 執行 Cathay 每日雲端技術情報掃描：從 AWS Blog / What's New / ML Blog 等 RSS 端點抓最新文章，透過五步管線（scan → compare → evaluate → validate → report）過濾出「今日 AI 選 3」給人類做最終決策，並附上 enterprise 案例對照。當使用者提到「今日雲端技術情報」、「每日掃描」、「AI 選 3」、「tech intel」、「AWS 新聞整理」、「技術情報日報」、「雲端技術評估」，或貼技術文章要求評估企業導入可行性、成熟度、AWS 契合度、案例佐證時，請務必使用此 skill——即使使用者沒明說「跑 pipeline」也要用。這個 skill 內建了主管的評估原則（不推薦太新的技術、驗證分離、案例對照）與 Cathay 的技術棧偏好（AWS 為主）。
---

# Cathay 雲端技術情報掃描

## 這是什麼

一個為 Cathay Life 雲端應用開發科設計的每日技術情報掃描系統。從 AWS 官方 RSS 端點抓最新文章，經過五步智慧漏斗過濾出「今日 AI 選 3」——附上 enterprise 案例對照與獨立驗證，讓決策者花 30 秒讀完就能決定要不要深入研究。

## 何時觸發

- 使用者要求「跑今日雲端技術掃描」、「AI 選 3」、「每日情報」
- 使用者貼一批技術文章要求評估企業導入可行性
- 使用者要對某個技術做「maturity / aws_fit / case evidence」評分
- 使用者要新增 RSS 來源或編輯掃描規則

## 核心原則（憲法）

執行時務必遵守以下設計原則，這些是主管明確要求的：

1. **不推薦太新的技術**：Preview / Beta 一律 L0 直接擋掉；剛 GA <3 個月的標記為「觀察區」不列 Top-3。
2. **驗證分離**：評估者（模型 A）不得驗證自己的產出。s3 用 Sonnet、s4 用 Haiku 交叉檢核，兩者權重刻意不同。
3. **案例佐證**：每個 Top-3 推薦必須引用至少一個 enterprise 案例，若無則明確標記「⚠ 無案例對照，信心度較低」。
4. **省 token**：L0 規則過濾 → L1 關鍵字粗排 → L2 才呼叫昂貴的 LLM 深度評估。前兩層擋掉 60%+ 的呼叫量。
5. **可稽核**：每一步都留 JSON 中間產物，人類可以回溯任何一個決策是怎麼來的。

## 環境需求

執行前確認：

```bash
# 1. Anthropic API key（呼叫 api.anthropic.com，不透過 Bedrock）
export ANTHROPIC_API_KEY="sk-ant-..."

# 2. Python 套件
pip install anthropic feedparser
```

若 `ANTHROPIC_API_KEY` 未設定，pipeline 會自動改跑 **rubric 模式**（用內建加權規則計分而非呼叫 LLM），適合本地驗證或 API 額度不足時的 fallback。

## 五步工作流程

### Step 1: 掃描（scan）— L0 規則過濾

執行 `scripts/rss_fetcher.py`，從 `data/sources.json` 定義的端點抓最新文章。

```bash
python scripts/rss_fetcher.py --sources data/sources.json --output out/raw.json
```

自動推論每篇文章的 tags、status（GA/Preview/Beta）、五維訊號（maturity/aws_fit/effort/risk）。無雲端 AI 相關關鍵字、Preview/Beta、14 天前、重複標題的一律剔除。

**輸出**：`out/raw.json` 含所有抓到的文章與 fetch_log；被剔除的項目和原因寫進 `out/s1_scan.json`。

### Step 2: 比對（compare）— L1 粗排取 Top-6

執行 `scripts/rank.py`，用需求關鍵字加權（如 bedrock=3.0, agent=2.5, guardrails=2.0）計算 L1 分數。跨雲對應表只在最後報告階段輸出，不作為第二條掃描入口。

```bash
python scripts/rank.py --input out/s1_scan.json --output out/s2_compare.json --top-k 6
```

**輸出**：Top-6 進入下一步深度評估，其餘剔除但保留 log。

### Step 3: 評估（evaluate）— L2 深度評估（建造者）

執行 `scripts/evaluate.py`，這一步呼叫 Anthropic API（預設 Claude Sonnet 4.5）對每篇文章做深度評分。同時對照 `data/case_studies/` 內的 enterprise 案例，計算 case_evidence 維度。

```bash
python scripts/evaluate.py \
    --input out/s2_compare.json \
    --cases data/case_studies/ \
    --output out/s3_evaluate.json \
    --model claude-sonnet-4-5
```

**評估者角色**：建造者。Rubric 權重 `{maturity: 0.35, aws_fit: 0.25, case_evidence: 0.15, effort: 0.15, risk: 0.10}`——maturity 為最高權重反映主管「不要太新」的原則。

**輸出**：全部評分 + Top-3 選擇。

### Step 4: 驗證（validate）— L2 獨立驗證（驗證者）

執行 `scripts/validate.py`，這一步呼叫**不同模型**（預設 Claude Haiku 4.5）獨立評分。這是憲法要求——建造者不得驗證自己。

```bash
python scripts/validate.py \
    --input out/s3_evaluate.json \
    --output out/s4_validate.json \
    --model claude-haiku-4-5
```

**驗證者權重刻意不同**：`{maturity: 0.20, aws_fit: 0.20, case_evidence: 0.20, effort: 0.20, risk: 0.20}`——五維均衡，偏保守。

**輸出**：驗證者的 Top-3、一致率、分歧項、硬規則旗標。若一致率 <67% 或有硬規則 flag 命中 Top-3，判定為「需人工複核」而非「通過」。

### Step 5: 報告（report）— 產出 HTML 日報

執行 `scripts/report.py` 彙整前四步的中間產物，產出可分享的 HTML 日報。

```bash
python scripts/report.py --run-dir out/ --output out/report.html
```

**輸出**：HTML 日報，主管有連結（或檔案）就能看，內含省 token 漏斗圖、Top-3 卡片、獨立驗證面板、案例引用、L0 剔除紀錄。

## 一鍵執行

若使用者要「跑完整條 pipeline」，用主腳本：

```bash
python scripts/run_pipeline.py --run-id $(date +%Y-%m-%d-%H)
```

會依序執行五步，中間產物寫到 `out/runs/{run_id}/`，最後開啟 `out/runs/{run_id}/report.html`。

## 如何調整

**新增/移除 RSS 來源**：編輯 `data/sources.json`，加一筆 `{"name": ..., "url": ..., "cloud": "aws", "enabled": true}`。

**調整 rubric 權重**：改 `scripts/evaluate.py` 頂端的 `W` 字典。若主管更在意風險，把 `risk` 從 0.10 拉高，其他等比降。

**切換模型**：`--model` 參數。目前 Cathay 相關脈絡建議：
- 建造者：`claude-sonnet-4-5`（能力強、成本適中）
- 驗證者：`claude-haiku-4-5`（快、便宜、不同尺寸達交叉檢核）

**新增案例**：見另一個 skill `case-study-registry`——不要在本 skill 內操作案例庫。

**Fallback 模式**：若 `ANTHROPIC_API_KEY` 未設定或 API 額度不足，pipeline 會自動改用 rubric 計分（見 `scripts/evaluate.py` 的 `--offline` 旗標）。

## 常見錯誤與排錯

| 症狀 | 可能原因 | 處理 |
|---|---|---|
| RSS 全部抓不到 | 網路問題 or 端點掛 | 自動 fallback 到 `data/fixtures/articles.json` |
| L2 評估拿 NaN | Anthropic API 失敗 | 每篇個別 fallback 到 rubric，log 標註 |
| 一致率永遠 100% | 建造者和驗證者用同一模型 | 檢查 `--model` 參數是否設不同模型 |
| 案例都沒對照上 | article tags 與 case matched_technologies 沒交集 | 檢查 tag 推論規則，或新增/更新案例 |

## 詳細架構與設計背景

若需深入了解憲法、五步管線的來由、案例庫如何影響評估、與 CDK 版部署的關係，讀 `references/pipeline-architecture.md`。
