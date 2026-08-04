---
name: report-cloud-evidence
description: Render S1 through S4 artifacts, PoC cost quotations, optional runtime evidence, into traceable JSON, Markdown, and GUI report models without adding unsupported claims. Use for Skill 5 interim or final technical reports, itemized quote sheets, evidence ledgers, verified-versus-unknown summaries, artifact lineage checks, or presentation-ready report data.
---

# Skill 5 · Report

Report recorded evidence. Do not fetch new sources, rescore candidates, infer missing facts, or operate AWS.

## Run

From `radar-redesign/`:

```powershell
python -m agentic_cloud_radar.cli s5 `
  --s1 .\out\run\s1.json `
  --s2 .\out\run\s2.json `
  --s3 .\out\run\s3.json `
  --s4 .\out\run\s4.json `
  --runtime .\out\run\s4-runtime-cleaned.json `
  --output .\out\run\s5-report.json `
  --markdown-output .\out\run\s5-report.md
```

`--runtime` is optional; omit it for interim reports before deployment or cleanup. There is no `--billing` input: this pipeline reports the pre-deployment estimate only and never reconciles it against actual AWS billing.

Reuse `agentic_cloud_radar/s5.py`.

## Workflow

1. Check stage presence, `run_id`, and candidate lineage.
2. Mark mismatched or missing required artifacts as `incomplete_artifacts`.
3. Summarize the Skill 3 score without recalculation and label it against the maximum score, for example `4.4 / 5`; do not show or derive a separate certainty metric.
4. Render the Skill 3 quote without recalculation: ID, validity, low/expected/high totals, expected scenario assumptions before line items, human-confirmed resource scope, the largest expected cost driver and what makes it increase, line items, and official sources.
5. Render the estimate as an estimate. Never present it as verified, reconciled, or invoiced.
6. If the S4 runtime includes `pre_cleanup_usage_snapshot`, render it as cleanup-before runtime usage evidence: elapsed time, CloudFormation resources, S3 object count/size, Lambda invokes/metrics when available, tags, and recipe-specific resource facts. Keep it separate from actual AWS cost.
7. Put verified facts under the technical validation status instead of a vague standalone section.
8. Show S1-S5 stage evidence explicitly, including S1 source fetch, S2 comparison evidence, S3 score/quote, S4 runtime/cleanup, and S5 report status.
9. Build an evidence source table linking claims to source or runtime artifacts.
10. Produce one JSON report, embedded Markdown, and a stable GUI model.
11. Mark the report `final` only when runtime status is `cleanup_verified`; for new `s4.runtime-evidence.v3`, Infrastructure Composer screenshot metadata and `display_channel_confirmed` must both be present. A cost-control abort is `final_without_console_review` with report type `closed_without_console_review`, never a normal actual-PoC final.

## Required report sections

- Candidate and official source.
- News summary focused on the new feature's application-side advantages.
- Skill 3 evaluation.
- PoC 成本估算報價單.
- cleanup 前即時用量快照.
- Skill 4 validation and runtime checks.
- 報價 vs 實際部署資源.
- Skill 4 資源盤點.
- 實際權限面.
- 各階段耗時.
- Console review outcome, including forced-cleanup reason and approver when applicable.
- Verified facts under 技術驗證狀態.
- Unknown or insufficiently supported claims.
- Future work: what else is worth doing for this news item and PoC.
- Reviewer questions: questions a reviewer would ask before trusting or extending the result.
- Human-useful related reading keywords.
- S1-S5 stage evidence.
- Evidence source table and S1-S4 funnel.

## Claim rules

- A named-human cost ceiling is not an official price.
- A public-price quotation is a non-binding estimate, not an AWS invoice or formal AWS sales quote.
- PoC quotes normally use monthly or usage-based public price units; when a PoC runs for only hours, the report must state the conversion basis. Lambda cost must be described as request and duration/GB-second based, not as an always-on charge.
- The Skill 3 quote is a static public-rate-card estimate unless `live_pricing_api_used=true`; it is not a real-time AWS Pricing API quotation.
- `recommend_poc` in artifacts means technically eligible for a controlled PoC, not proof that the candidate fits the company's workload.
- Runtime duration, CloudFormation status, and cleanup status are not cost evidence.
- `pre_cleanup_usage_snapshot` is immediate runtime evidence only; it may support the cost explanation but must never be converted into an actual AWS cost.
- The quote is never validated against AWS billing in this pipeline. State that limitation explicitly rather than implying the figure was confirmed.
- The billing method and formula of each line item must be shown, so a reviewer can check the calculation itself.
- Do not omit zero-charge recipe resources, usage assumptions, exclusions or source URLs.
- `CREATE_COMPLETE` is deployment evidence, not cleanup evidence.
- A `deployed_not_quoted` row means the quote omitted a resource the run really creates. Report it as a quote defect, not a rounding difference.
- The permission surface covers only the tested recipe; it is not the full production permission set.
- Report machine time and human wait separately. Never combine them into one elapsed figure.
- Console screenshot metadata proves only that a redacted PNG was captured and hashed. `display_channel_confirmed` records where the named human actually saw it; the program does not inspect image content, so the named human confirmation carries that judgment.
- A forced cleanup is cost control, not proof that the deployed stack received Console review.
- Sandbox evidence proves only the tested recipe and workload; do not generalize it to every environment.
- Missing evidence must remain `unknown`.

## Validation

```powershell
python -m unittest tests.test_s5 -v
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


## 各階段計時

每個 CLI 指令都會被計時，結果寫回該指令產出的 artifact，並隨流程往下傳遞。
不需要額外的狀態檔，換一台電腦接手也不會遺失。

兩個時鐘分開記錄：

| 欄位 | 意義 |
|---|---|
| `machine_seconds` | 程式運算與擷取耗時 |
| `human_wait_seconds` | 停留在人工關卡的時間 |

**人工等待由程式推導，不由人填寫**：

- S3 的等待 = 核准文件的 `approved_at` − S3 的 `ended_at`
- S4 的等待 = 盤點確認的 `confirmed_at` − S4 的 `ended_at`

要人自己記錄花了多久，正是這套流程要消除的「額外做事」，而且自填的數字不構成證據。

重跑同一階段時，保留最初的 `started_at`、更新 `ended_at`、`attempt_count` 加一——
取最後一次，不累加重疊區間。跨主機的區間會標記 `cross_host`，報告據此加註時鐘差異的但書。

`time_to_first_success_seconds` 從 S1 起算到 S4 首次驗證通過。
