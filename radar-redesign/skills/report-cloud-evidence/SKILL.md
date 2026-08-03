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
3. Summarize the Skill 3 score without recalculation and label it against the maximum score, for example `4.4 / 5`; do not show confidence in the human-facing summary.
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
- Automated checks do not replace Console review.
- Console screenshot metadata proves only that a redacted PNG was captured and hashed. `display_channel_confirmed` records where the named human actually saw it; the program does not inspect image content, so the named human confirmation carries that judgment.
- A forced cleanup is cost control, not proof that the deployed stack received Console review.
- Sandbox evidence proves only the tested recipe and workload; do not generalize it to every environment.
- Missing evidence must remain `unknown`.

## Validation

```powershell
python -m unittest tests.test_s5 -v
```
