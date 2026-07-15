---
name: case-study-registry
description: 管理 Cathay 技術評估用的 enterprise 案例庫——新增、搜尋、更新案例，計算對 Cathay 的相關性。當使用者說「新增一個案例」、「查詢有沒有 XX 產業的案例」、「這技術有沒有企業導入過」、「把 XX 公司的案例加進去」、「更新案例的相關性分數」、「列出所有金融業案例」時使用。案例庫是評估邏輯的核心——tech-intel-scan skill 會用它做 few-shot grounding，所以維護案例的品質很重要。
---

# Cathay 案例庫管理（Case Study Registry）

## 這是什麼

管理一組結構化的 enterprise 導入案例，供 `tech-intel-scan` skill 做評估對照用。每個案例是一份 JSON，記錄：
- 客戶、產業、地區、年份
- 使用的 AWS 服務、匹配技術標籤
- 導入方式、成效、合規對應
- **對 Cathay 的相關性分數（1-5）** ← 這是評估時的關鍵欄位

## 何時觸發

- 使用者要新增一個案例（貼案例網址或文字描述）
- 使用者要查詢某產業/技術/客戶的相關案例
- 使用者要更新案例的相關性分數
- tech-intel-scan skill 執行時需要案例對照

## 案例 Schema

每個案例是 `case_studies/{ID}.json`，欄位如下：

```json
{
  "id": "SBI-Life-Insurance-2024",
  "customer": "SBI 生命保險株式會社",
  "industry_tags": ["insurance", "life-insurance", "highly-regulated", "APAC"],
  "region": "Japan",
  "year": 2024,
  "system": "客服中心文件檢索系統",
  "partner": "AWS 直接合作",
  "aws_services": ["Amazon Bedrock", "Amazon Kendra"],
  "matched_technologies": ["bedrock", "rag", "knowledge-base", "llm", "embedding"],
  "approach": "2023 年 7 月小規模試點 → 2024 年幾乎全員使用",
  "outcomes": ["客服人員可快速跨多種文件回應", "訓練時間縮短約 30%"],
  "compliance_signals": ["日本金融監管合規"],
  "relevance_to_cathay": {
    "score": 5,
    "reason": "同為亞洲人壽保險業、同為受金融監管——與 Cathay Life 情境幾乎一對一對應"
  },
  "source": "AWS 官方案例研究",
  "key_takeaways": [
    "從小規模試點開始，逐步擴大到全員",
    "客服文件檢索是保險業導入 GenAI 的低風險高價值切入點"
  ]
}
```

## 工作流程

### 新增案例

當使用者要新增案例，執行以下步驟：

1. **收集資訊**：詢問客戶名稱、產業、年份、使用的 AWS 服務、關鍵成效。若使用者只給 URL，Claude 應該用 web_fetch 或 web_search 讀原文再抽取結構化資訊。

2. **推論 matched_technologies**：從 aws_services 反推 tag（例如「Amazon Bedrock」→ `bedrock`；「Bedrock Knowledge Bases」→ `bedrock, rag, knowledge-base`）。這些 tag 會決定案例會不會被 tech-intel-scan 匹配到。

3. **評估對 Cathay 的相關性（1-5）**，判斷標準：
   - **5/5**：同產業（保險/金融）+ 同監管等級 + 同技術方向
   - **4/5**：符合其中兩項
   - **3/5**：符合其中一項
   - **2/5**：僅通用參考價值
   - **1/5**：關聯度低但有啟發

4. **執行 `scripts/add_case.py`** 建立案例檔：

```bash
python scripts/add_case.py \
    --id "SBI-Life-Insurance-2024" \
    --data path/to/case.json \
    --out data/case_studies/
```

### 搜尋案例

```bash
# 依產業
python scripts/search_cases.py --industry insurance

# 依技術
python scripts/search_cases.py --tag bedrock

# 依對 Cathay 相關性
python scripts/search_cases.py --min-relevance 4
```

### 更新案例相關性

若使用者說「XX 案例的相關性應該調到 5」或發現原本評估有誤：

1. 打開 `case_studies/{ID}.json`
2. 修改 `relevance_to_cathay.score` 和 `reason`
3. 存檔即可，tech-intel-scan skill 下次執行會自動撿到新分數

## 品質原則

- **來源要可查證**：AWS 官方 blog、案例研究、產業媒體優先。禁止用「聽說」的案例。
- **相關性分數要保守**：寧可低估、不要高估。5/5 是「幾乎一對一對應」，不是「大概有像」。
- **失敗案例也收**：反面教材對評估同樣重要。若加入失敗案例，在 `outcomes` 中誠實記錄，並在 `key_takeaways` 加「⚠ 失敗警示」。
- **定期老化**：3 年以上的案例應在 review 時決定要不要降權（AWS 服務演化快）。

## 建議來源

- AWS 官方案例：https://aws.amazon.com/solutions/case-studies/
- AWS 金融服務案例：https://aws.amazon.com/financial-services/case-studies/
- AWS 產業部落格：https://aws.amazon.com/blogs/industries/
- Cathay 內部 POC 紀錄（若有）
