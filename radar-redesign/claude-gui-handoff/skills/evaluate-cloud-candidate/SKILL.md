---
name: evaluate-cloud-candidate
description: Evaluate Skill 2 candidates with the fixed Skill 3 public-evidence rubric and produce auditable reusable PoC cost quotations. Use when a person needs a reproducible score, risk analysis, cost estimate, and a merged human PoC decision gate before any controlled Skill 4 PoC.
---

# Skill 3 · Evaluate

Evaluate only one human-selected candidate. Do not silently select candidates or require custom environment forms.

## Inputs

- S2 comparison artifact with a stable `run_id`.
- Human selection request naming exactly one S2 candidate ID (`.\out\run\shortlist.json`).

Human candidate selection is mandatory. Public-evidence evaluation does not require a business problem, environment description, or data-boundary form.

## Run

From `radar-redesign/`:

```powershell
python -m agentic_cloud_radar.cli s3 `
  --input .\out\run\s2.json `
  --shortlist .\out\run\shortlist.json `
  --output .\out\run\s3.json
```

Reuse the fixed rubric in `agentic_cloud_radar/s3.py`.

## Workflow

1. Verify S2 lineage and candidate IDs.
2. Evaluate every S2 candidate by default. Treat `--shortlist` only as an optional filter, not as approval.
3. Score only evidence-supported dimensions with the fixed rubric.
4. Record weighted score, Region state, governance flags, stop conditions, and evidence limits.
5. For every evaluated candidate, create the entire PoC quote before Skill 4: low/expected/high usage, itemized rates, formulas, official sources, validity, exclusions, quoted Region, `live_pricing_api_used`, and a recommended approval ceiling.
   - Level A: use a registered candidate-specific PoC recipe and rate card.
   - Level B: when no registered cost recipe exists but S2/IaC/service evidence identifies billable AWS services, use the reusable generic usage model and mark `pricing_level=Level B generic usage model`.
   - Level C: when the service/resource scope is still too vague, return `status=incomplete` with missing inputs instead of inventing a number.
6. Set the one decision field, `recommend_poc`, only when the score is `>= 3.75` on the 5-point weighted rubric, no PoC blocker exists, and the quote status is `estimated`. Treat this field as technical eligibility for a controlled PoC, not proof of workload fit or permission to deploy.
7. Populate `poc_decision_gate` with every evaluated option, including score, quote status, low/expected/high estimate, recommended approval ceiling, blocker list, the PoC proof question, and the required human outputs: `selected_candidate_id`, `approved_by`, `approved_cost_ceiling_usd`.
8. When writing the optional Skill 3 PoC decision report, explain the article before the approval decision: what changed, why it matters, key source-backed points, and the inferred minimal implementation architecture.
9. Before showing the PoC score and quote, show the PoC proof question: "What does this PoC need to prove, and what will the decision-maker know if it succeeds?" Answer it in concrete evidence terms such as deployability, Region/account compatibility, IAM/resource wiring, runtime behavior, cleanup repeatability, or limits that remain unknown. If this cannot be answered, Skill 3 must not recommend moving to Skill 4 even when the numeric score is high.
10. After the proof question, show PoC threshold, score, quote, recipe, blockers, and what Cleo must approve before Skill 4.
11. Keep Region and pricing uncertainty in `poc_review_notes`; do not require the user to configure an environment.
12. `recommend_s4` is an input-only compatibility fallback for old artifacts. New S3 artifacts do not produce low-risk or separate paid-PoC decision fields.

## Guardrails

- Do not use a separate certainty score as a PoC eligibility gate. Use score threshold, blockers, quote readiness, deployable recipe, and named human approval.
- PoC blocker codes are concrete stop conditions such as `not_ga`, `no_public_source`, `forbidden_service`, `incomplete_cost_quote`, `no_registered_poc_recipe`, `target_region_unavailable`, `unsafe_permissions`, or `production_data_required`.
- Cost estimation and deployment recipe registration are separate gates. Skill 3 may produce a Level B generic estimate for review; Skill 4 deployment context must still block real AWS resource creation with `needs_poc_recipe` until a deployable recipe exists.
- Do not award points from an unverified static case study.
- Do not convert `region_unknown` into unavailable or available.
- Do not call a human-approved spending ceiling an official estimate.
- Do not call a public-price estimate an AWS invoice, tax invoice or binding sales quote.
- Treat the quote as a static public rate-card estimate unless `live_pricing_api_used=true`; it is not a real-time AWS Pricing API result by default.
- Keep cost outside the technical rubric score.
- Do not describe a rubric fallback as an LLM or external API result.
- Do not infer workload fit from public evidence; report it as not assessed.

## Validation

```powershell
python -m unittest tests.test_s3_s4 -v
```

## Stage closure checklist

Before ending the Skill run, complete and report this checklist so the human does not have to chase basic closure:

- Update `AI_PM_INBOX.md` or the formal daily log with the stage outcome, evidence, blockers, and next step.
- Update `README.md`, `MIGRATION_STATUS.md`, or another handoff document when the run changes project state or cross-computer continuity.
- Run the relevant validation command, or state clearly why it could not be run.
- Check `git status --short` and identify whether changes are expected.
- Commit meaningful completed work.
- Push the branch when the work is meant to be shared.
- Verify the pushed state is visible on GitHub before claiming it is synced.
- Leave the next required human or AI action in plain Traditional Chinese.

## Merged decision gate

S3 ends with `poc_decision_gate`, the only human gate before Skill 4. It lists every candidate with weighted score out of 5, Region state, quote status, expected total, recommended ceiling, technical eligibility, and blockers, so one person decides both questions at once: which candidate, and whether the estimated cost is worth spending.

Required human outputs: `selected_candidate_id`, `approved_by`, `approved_cost_ceiling_usd`. Technical eligibility is never approval.

## PoC proof question

Before Skill 4 approval, the report must answer in plain Traditional Chinese:

- What exactly is this PoC trying to prove?
- If it succeeds, what new decision evidence will the reviewer have that Skill 3 alone did not provide?
- Which questions will still remain unanswered after this small PoC?

Valid answers are concrete and testable: for example, that the feature can be deployed in the target Region, the recipe creates the expected resource relationships, the permission surface is bounded, the runtime check actually passes, cleanup is repeatable, or a specific integration behavior works. Invalid answers are vague value statements such as "prove it is useful", "prove the article is valuable", or "prove it should be adopted".

## Cost scope

The quote is a pre-deployment public-rate-card estimate. This pipeline does not collect actual AWS billing and never reconciles estimate against invoice, so the billing method and formula for every line item must be correct on their own: monthly-rate resources prorated by PoC hours, request-priced resources by request count, Lambda charged only per invocation plus GB-seconds. Do not omit any resource the recipe creates, including default CloudWatch log groups.

Pass the S3 artifact to `$validate-cloud-poc`.


## 與 Skill 4 的銜接

每個評估候選都帶 `poc_recipe`（registry 的判定）與 `s4_readiness`（給人看的結論）。

候選若沒有可部署 recipe，報告必須同時說清楚四件事，不可只寫「不行」：

- 技術上值得評估
- 但目前不能進入 Skill 4
- 原因是缺少專用 recipe（或只有草案）
- **下一步是建立 recipe，不是建立 AWS 資源**

`recommend_poc=true` 只代表技術資格，不代表可以部署。可否部署由
`s4_readiness.can_enter_skill4` 決定，來源是
`agentic_cloud_radar/s4_recipes/registry.py`。

machine-readable 的 key 一律使用英文：`can_enter_skill4`、`readiness_status`、
`technical_assessment_zh`、`reason_zh`、`next_step_zh`、`authoring_template`、
`recipe_decision`。中文只出現在值與報告文字中。

決策報告在本輪沒有任何可部署 recipe 時，**不得**出現「請回覆同意進入 Skill 4」，
必須改寫為「技術上值得評估，但目前不能進 Skill 4；下一步是建立或補齊專用
recipe，不是建立 AWS 資源」。

Skill 3 不得以通用成本模型作為進入 Skill 4 的依據。


## 評分準則的單一來源

構面定義、逐級判定條件、權重與否決門檻全部宣告在
`agentic_cloud_radar/rubric.py`。說明文件由同一份定義產生：

```powershell
python -m agentic_cloud_radar.cli rubric --output docs\評分準則.md
```

因此文件不可能與實際行為不一致——兩者讀的是同一份資料。完整的逐級條件見
[`docs/評分準則.md`](../../docs/評分準則.md)。

### 三條不可違反的規則

**不得為特定候選寫死分數。** 每一級的判定條件都必須是任何候選都適用的訊號。
若某個候選得到不合理的分數，要修的是訊號定義，不是為它加一個分支——否則評分準則
就退化成查表，個案結果也不能作為方法有效的證據。`tests/test_rubric.py` 有守門測試
掃描原始碼，出現特定產品名即失敗。

**證據不足與表現不佳要分開。** 缺乏證據時給中間值並在理由中標明；確實表現差才落到
否決門檻。混為一談會讓「文件寫得少」看起來像「技術不好」。

**每個分數都要附判定理由。** `dimension_details` 逐項記錄得分、權重、加權值與理由，
報告以表格呈現。單一加權數字無法被質疑，細目才能讓審查者針對特定構面提出異議。

### 報告須標示資訊來源

每份決策報告都包含「本報告的資訊來源」表，逐階段列出實際欄位：
S1 提供原文與解釋層、S2 提供比較與提案卡、S3 產生分數與報價。

讀報告的人若分不出來，就會把 S3 的推導當成 AWS 的原文陳述——那正是這套流程
最想避免的事。
