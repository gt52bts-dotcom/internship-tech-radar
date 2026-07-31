---
name: report-cloud-evidence
description: Render S1 through S4 artifacts, PoC cost quotations, optional runtime evidence, and optional attributable AWS billing evidence into traceable JSON, Markdown, and GUI report models without adding unsupported claims. Use for Skill 5 interim or final technical reports, itemized quote sheets, estimate-versus-actual cost reconciliation, evidence ledgers, verified-versus-unknown summaries, artifact lineage checks, or presentation-ready report data.
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
  --billing .\out\run\cost-explorer-attribution.json `
  --output .\out\run\s5-report.json `
  --markdown-output .\out\run\s5-report.md
```

`--runtime` and `--billing` are optional. Omit `--runtime` for interim reports before deployment or cleanup. Omit `--billing` when Cost Explorer, Billing, or CUR evidence is not yet attributable to the run; Skill 5 must then show actual cost as `pending`.

Reuse `agentic_cloud_radar/s5.py`.

## Workflow

1. Check stage presence, `run_id`, and candidate lineage.
2. Mark mismatched or missing required artifacts as `incomplete_artifacts`.
3. Summarize the Skill 3 score and confidence without recalculation.
4. Render the Skill 3 quote without recalculation: ID, validity, low/expected/high totals, expected line items, assumptions, exclusions and official sources.
5. Compare the public-price estimate with actual AWS cost only if an attributable Billing, Cost Explorer, or CUR artifact is provided.
6. If the S4 runtime includes `pre_cleanup_usage_snapshot`, render it as cleanup-before runtime usage evidence: elapsed time, CloudFormation resources, S3 object count/size, Lambda invokes/metrics when available, tags, and recipe-specific resource facts. Keep it separate from actual AWS cost.
7. Separate verified facts from unknown or unverified statements.
8. Build an evidence ledger linking claims to source, runtime, or billing artifacts.
9. Produce one JSON report, embedded Markdown, and a stable GUI model.
10. Mark the report `final` only when runtime status is `cleanup_verified`; for new `s4.runtime-evidence.v3`, Infrastructure Composer screenshot metadata and `display_channel_confirmed` must both be present. A cost-control abort is `final_without_console_review` with report type `closed_without_console_review`, never a normal actual-PoC final.

## Required report sections

- Candidate and official source.
- One-sentence conclusion.
- Skill 3 evaluation.
- PoC 成本估算報價單.
- 預估成本 vs 可歸因實際帳務成本.
- cleanup 前即時用量快照.
- Skill 4 validation and runtime checks.
- Console review outcome, including forced-cleanup reason and approver when applicable.
- Verified facts.
- Unknown or insufficiently supported claims.
- Next reminders.
- Evidence ledger and S1-S4 funnel.

## Claim rules

- A named-human cost ceiling is not an official price.
- A public-price quotation is a non-binding estimate, not an AWS invoice or formal AWS sales quote.
- The Skill 3 quote is a static public-rate-card estimate unless `live_pricing_api_used=true`; it is not a real-time AWS Pricing API quotation.
- `recommend_poc` in artifacts means technically eligible for a controlled PoC, not proof that the candidate fits the company's workload.
- Runtime duration, CloudFormation status, and cleanup status are not actual billing evidence.
- `pre_cleanup_usage_snapshot` is immediate runtime evidence only; it may support the cost explanation but must never be converted into actual AWS billing cost.
- If no attributable Cost Explorer, Billing, or CUR artifact is present, actual cost must remain `pending`.
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
