# S4 Recipe 撰寫範本

遇到沒有 recipe 的 AWS 新功能時，照這份填完，就能新增一份 recipe，不用改動 Skill 4 本體。

**兩條不可跨越的線：**

1. **沒填完不得部署。** 未填完的 recipe 一律註冊為草案（`deployable=False`），registry 會拒絕交給部署器。
2. **不得臨場補寫後直接部署。** 新 recipe 必須先進 registry、通過測試、由人審過，才可能用於實際部署。

---

## 第零步：先確認這個 PoC 值得做

這三題答不出來就不要寫 recipe。**分數高不是理由。**

**這個 PoC 要證明什麼？**
> 必須是具體、可測的證據。例如：部署可行性、目標區域與帳號相容性、資源關係、權限邊界、runtime 行為、cleanup 可重現性。

**成功之後，決策者會多知道什麼？**
> 如果答案是「知道它能動」，而官方文件已經這樣寫了，那這個 PoC 沒有增加資訊。

**Skill 3 已經能回答什麼？Skill 4 才需要補什麼？**
> 只有第二欄才是這個 recipe 的存在理由。若第二欄是空的，不要進 Skill 4。

---

## 第一步：填寫 recipe 契約

在 `agentic_cloud_radar/s4_recipes/registry.py` 新增一個 `RecipeDefinition`。

| 欄位 | 填什麼 | 常見錯誤 |
|---|---|---|
| `recipe_id` | 小寫底線，結尾標示形式（`_cdk` / `_draft`） | 用顯示名稱當 id |
| `display_name` / `display_name_zh` | 一句話說清楚驗證什麼 | 只寫服務名稱 |
| `supported_candidate_patterns` | 比對用字串；`service:X` 可比對偵測到的服務 | 用過於通用的字（如 `aws`）造成誤配 |
| `required_aws_services` | 部署會用到的服務，**含 IAM 與 CloudWatch** | 漏掉文章沒提但實作必需的 |
| `required_region_capabilities` | 這個功能在區域層級需要什麼 | 只寫服務有沒有端點 |
| `estimated_cost_model_id` | 對應 `costing.py` 的成本模型 | **填通用模型** ← 禁止 |
| `deployable_resource_types` | CloudFormation 資源型別全名 | 漏掉 IAM Role、Log Group |
| `required_iam_actions` | 實際會呼叫的 action | 用萬用字元 |
| `approval_required_fields` | 人工必填欄位 | 少了核准上限 |
| `deployment_inputs_schema` | 部署參數與預設值 | 允許自由指定堆疊名稱 |
| `success_criteria` | 可觀察、可判定的條件 | 寫「運作正常」 |
| `evidence_to_collect` | 要留下哪些證據 | 只留成功訊息 |
| `cleanup_strategy` | 怎麼清、順序為何 | 沒處理 bucket 內物件 |
| `cleanup_verification` | 清完怎麼回查 | 只看 delete 指令有沒有報錯 |
| `risk_level` | `low` / `medium` / `high` | 一律填 low |
| `stop_conditions` | 什麼情況必須停止 | 留空 |
| `unsupported_conditions` | 什麼情況本 recipe 不適用 | 留空 |

### 成本模型怎麼算

在 `costing.py` 新增對應模型，並確認：

- 月費型資源依 PoC 使用時數折算
- 請求型資源依請求量計算
- **不要漏掉服務自動建立的資源**（例如 Lambda 的預設 log group）
- `priced_resource_types` 必須與 `deployable_resource_types` 對得起來

Skill 4 的資源盤點會自動比對兩者。出現 `deployed_not_quoted` 就代表報價漏列，**必須修正資源清單，不是調整金額**。

---

## 第二步：建立 PoC 專案

在 `poc/<recipe-name>/` 放 CDK 專案，並把路徑填入 `poc_directory`。

- 堆疊名稱必須由 `run_id` 推導，不可自由指定
- 只建立沙箱資源，不碰既有資源
- 不寫入任何正式環境資料

---

## 第三步：寫測試

在 `tests/test_s4_recipes.py` 至少加：

- 新 recipe 能被正確候選比對到
- 契約無缺漏（`contract_gaps()` 為空）
- 草案不可部署
- 部署前檢查在缺少核准或區域承認時會擋下

---

## 第四步：人工審查

新 recipe 進入可部署前，須由具名人員確認：

- [ ] 第零步三題都答得出來
- [ ] `cleanup_strategy` 涵蓋所有會建立的資源
- [ ] `required_iam_actions` 沒有萬用字元
- [ ] `stop_conditions` 涵蓋成本失控與驗證逾時
- [ ] 成本模型與 `deployable_resource_types` 一致
- [ ] `risk_level` 反映真實風險

---

## 草案怎麼寫

尚無法部署時，仍應登錄為草案，把已知的設計工作留下來：

```python
deployable=False,
needs_region_confirmation=True,
needs_environment_preparation=True,
needs_cost_model=True,
draft_notes=(
    "若要實作，至少需要：……",
),
```

草案的價值在於**讓下一個人不必從零開始**，也讓 Skill 3 報告能明確說出「缺什麼」而不只是「不行」。

參考 `workspaces_ai_agent_access_draft`。
