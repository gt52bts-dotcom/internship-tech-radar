---
name: evaluate-cloud-candidate
description: 使用固定 Skill 3 public-evidence rubric 評估 Skill 2 候選，並產出可稽核、可重用的 PoC 成本估算。適用於需要可重現分數、風險分析、成本估算，以及進入任何 Skill 4 受控 PoC 前的 merged human decision gate。
---

# Skill 3 Evaluate：單一候選評估與 PoC 決策

Skill 3 只評估人類選定的一個候選。它不默默幫人選候選，也不要求使用者填公司環境表單。

## 核心定位

Skill 3 的任務是把「看起來值得」轉成「是否值得核准受控 PoC」的決策。

它回答三個問題：

- 這個候選以公開證據來看，技術分數是多少？
- 如果要做 PoC，這次到底要證明什麼？
- 估算成本、風險、停止條件與 cleanup 是否足以讓人核准 Skill 4？

## 輸入

- S2 comparison artifact，必須有穩定 `run_id`。
- 人類選擇請求，必須指定剛好一個 S2 candidate ID，例如 `.\out\run\shortlist.json`。

人類選候選是必要的。Public-evidence evaluation 不需要額外 business problem、environment description 或 data-boundary form。

## 執行方式

從 `radar-redesign/` 執行：

```powershell
python -m agentic_cloud_radar.cli s3 `
  --input .\out\run\s2.json `
  --shortlist .\out\run\shortlist.json `
  --output .\out\run\s3.json `
  --decision-report-html-output .\out\run\skill3-poc-decision-report.html `
  --decision-report-image .\out\run\skill3-poc-architecture.png
```

評分邏輯必須重用 `agentic_cloud_radar/s3.py` 與 `agentic_cloud_radar/rubric.py`，不要在 Skill 文件中另寫一套。

## 工作流程

1. 確認 S2 lineage 與 candidate ID。
2. 預設評估所有 S2 candidate；`--shortlist` 只是可選 filter，不是核准。
3. 只用有證據支撐的維度評分，並使用固定 rubric。
4. 記錄 weighted score、Region state、governance flags、stop conditions 與 evidence limits。
5. 對每個被評估候選，在 Skill 4 前建立完整 PoC quote：low/expected/high usage、itemized rates、formulas、official sources、validity、exclusions、quoted Region、`live_pricing_api_used` 與 recommended approval ceiling。
6. 成本模型分三級：
   - Level A：有 registered candidate-specific PoC recipe 和 rate card。
   - Level B：沒有 registered cost recipe，但 S2/IaC/service evidence 已能辨識可計費 AWS 服務時，用 reusable generic usage model，並標記 `pricing_level=Level B generic usage model`。
   - Level C：服務或資源範圍仍太模糊時，回傳 `status=incomplete` 與 missing inputs，不要編造金額。
7. 只有在 weighted score `>= 3.75 / 5`、沒有 PoC blocker、quote status 是 `estimated` 時，才設定 `recommend_poc=true`。這只代表技術上具備受控 PoC 資格，不代表已適合公司工作負載，也不是部署授權。
8. 填入 `poc_decision_gate`，列出每個 option 的 score、quote status、low/expected/high estimate、recommended approval ceiling、blockers、PoC proof question，以及人類必填的 `selected_candidate_id`、`approved_by`、`approved_cost_ceiling_usd`。
9. 產生 optional Skill 3 PoC decision report 時，先用繁中解釋文章內容：發生什麼改變、為什麼重要、有哪些 source-backed key points、推論出的最小實作架構是什麼。
10. 在分數和報價前，插入人類可讀的 PoC minimum architecture PNG。若候選已有 registered Skill 4 recipe，圖中要畫 Skill 4 真的會建立或驗證的資源；若沒有 recipe，圖只能呈現 S1 inferred architecture，且必須標成 draft，不是可部署 production architecture。
11. 顯示 PoC proof question：這次 PoC 要證明什麼？如果成功，決策者會多知道什麼？答案必須是可測的 evidence，例如 deployability、Region/account compatibility、IAM/resource wiring、runtime behavior、cleanup repeatability，或仍未知的限制。
12. proof question 之後，才顯示 PoC threshold、score、quote、recipe、blockers，以及 Cleo 進 Skill 4 前必須核准的內容。
13. Region 和 pricing uncertainty 留在 `poc_review_notes`；不要要求使用者額外配置環境表單。
14. `recommend_s4` 只作為舊 artifact 的 input compatibility fallback。新的 Skill 3 artifact 不再產生 separate low-risk 或 paid-PoC decision field。

## 評分與決策規則

- 不使用獨立 confidence score 作為 PoC eligibility gate。PoC eligibility 由 score threshold、blockers、quote readiness、deployable recipe 與 named human approval 決定。
- PoC blocker 必須是具體停止條件，例如 `not_ga`、`no_public_source`、`forbidden_service`、`incomplete_cost_quote`、`no_registered_poc_recipe`、`target_region_unavailable`、`unsafe_permissions`、`production_data_required`。
- 成本估算和部署 recipe registration 是兩個不同 gate。Skill 3 可以產生 Level B generic estimate 供 review，但 Skill 4 deployment context 仍必須在沒有 deployable recipe 時以 `needs_poc_recipe` 阻擋真實 AWS resource creation。
- 不要從未驗證的 static case study 加分。
- 不要把 `region_unknown` 自行轉成 available 或 unavailable。
- 人類核准的 spending ceiling 不是官方估價。
- Public-price estimate 不是 AWS invoice、tax invoice 或 binding sales quote。
- quote 預設是 static public rate-card estimate；除非 `live_pricing_api_used=true`，否則不是 real-time AWS Pricing API 結果。
- 成本不進入 technical rubric score。
- 不要把 rubric fallback 描述成 LLM 或外部 API 結果。
- 不要從公開證據推論 workload fit；它只能標為 not assessed。

## HTML decision report

Skill 3 的人類審查報告預設是 HTML。請先生成或提供 GPT-style architecture PNG，再用 `--decision-report-image` 傳入 CLI，讓 HTML 以 data URI 內嵌圖片。

Markdown 可以保留為內部 fallback，但不是主要 review artifact。若已生成 PNG，不要再把舊 Mermaid/text flowchart 放進人類版報告。

## Merged decision gate

Skill 3 以 `poc_decision_gate` 結束，這是進 Skill 4 前唯一的人類 gate。它會列出每個候選的 `5` 分制 weighted score、Region state、quote status、expected total、recommended ceiling、technical eligibility 與 blockers，讓同一個人一次決定兩件事：

- 選哪一個 candidate。
- 估算成本是否值得花。

必要人類輸出：

- `selected_candidate_id`
- `approved_by`
- `approved_cost_ceiling_usd`

Technical eligibility 永遠不等於 approval。

## PoC proof question

進 Skill 4 前，報告必須用繁中回答：

- 這個 PoC 到底要證明什麼？
- 如果成功，reviewer 會多得到哪個 Skill 3 還沒有的決策證據？
- 這個小 PoC 做完後，哪些問題仍然不能宣稱已解決？

有效答案必須具體且可測，例如：

- 目標 Region 可部署。
- recipe 建立了預期 resource relationship。
- permission surface 有邊界。
- runtime check 真的通過。
- cleanup 可以重現。
- 某個 integration behavior 可以運作。

無效答案包含：「證明它有用」、「證明文章有價值」、「證明應該採用」。

## 成本範圍

quote 是 pre-deployment public-rate-card estimate。本 pipeline 不收集 actual AWS billing，也不把 estimate 和 invoice 對帳。

每個 line item 的 billing method 和 formula 必須能獨立檢查：

- 月費型資源依 PoC 小時數 prorate。
- request-priced resources 依 request count。
- Lambda 只依 invocation 與 duration / GB-second 計費，不是 always-on。
- 不可漏列 recipe 會建立的資源，包括 default CloudWatch log groups。

## Skill 4 readiness

Skill 3 會輸出 `poc_recipe` 與 `s4_readiness`，說明候選能不能進 Skill 4。

重點規則：

- `recommend_poc=true` 代表技術上值得受控 PoC，但不等於可以部署。
- 真正能否進 Skill 4，要看 `s4_readiness.can_enter_skill4`，來源是 `agentic_cloud_radar/s4_recipes/registry.py`。
- 沒有 deployable recipe 時，報告應清楚說明下一步是撰寫 recipe，不是硬進 Skill 4。

機器可讀欄位包括：

- `can_enter_skill4`
- `readiness_status`
- `technical_assessment_zh`
- `reason_zh`
- `next_step_zh`
- `authoring_template`
- `recipe_decision`

## 評分準則文件

評分準則唯一來源是 `agentic_cloud_radar/rubric.py`。若需要輸出文件：

```powershell
python -m agentic_cloud_radar.cli rubric --output docs\評分準則.md
```

不要在文件中手寫另一套 rubric，否則會和實際評分程式分歧。

## 驗證

```powershell
python -m unittest tests.test_s3_s4 -v
```

## 階段收尾清單

結束 Skill 3 前，必須完成並回報：

- 更新 `AI_PM_INBOX.md` 或正式 daily log，記錄階段成果、證據、blocker 與下一步。
- 若本次改變專案狀態或跨電腦交接內容，更新 `README.md`、`MIGRATION_STATUS.md` 或其他 handoff 文件。
- 執行相關驗證指令，若無法執行要說明原因。
- 檢查 `git status --short`，並說明變更是否符合預期。
- 在需要共享時提交有意義的 commit。
- 需要同步時 push branch。
- 宣稱已同步前，確認 GitHub 上看得到 pushed state。
- 用清楚繁中留下下一個人類或 AI 需要做的動作。

## 下一階段

把 `s3.json` 交給 `$validate-cloud-poc`。
