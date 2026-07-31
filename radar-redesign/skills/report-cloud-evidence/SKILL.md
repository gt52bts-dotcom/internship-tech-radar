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
  --s1 .\out\s1.json `
  --s2 .\out\s2.json `
  --s3 .\out\s3.json `
  --s4 .\out\s4.json `
  --runtime .\out\run\s4-runtime-cleaned.json `
  --billing .\out\cost-explorer-attribution.json `
  --output .\out\s5-report.json `
  --markdown-output .\out\s5-report.md
```

`--runtime` and `--billing` are optional. Omit `--runtime` for interim reports before deployment or cleanup. Omit `--billing` when Cost Explorer, Billing, or CUR evidence is not yet attributable to the run; Skill 5 must then show actual cost as `pending`.

Reuse `agentic_cloud_radar/s5.py`.

## Workflow

1. Check stage presence, `run_id`, and candidate lineage.
2. Mark mismatched or missing required artifacts as `incomplete_artifacts`.
3. Summarize the Skill 3 score and confidence without recalculation.
4. Render the Skill 3 quote without recalculation: ID, validity, low/expected/high totals, expected line items, assumptions, exclusions and official sources.
5. Compare the public-price estimate with actual AWS cost only if an attributable Billing, Cost Explorer, or CUR artifact is provided.
6. Separate verified facts from unknown or unverified statements.
7. Build an evidence ledger linking claims to source, runtime, or billing artifacts.
8. Produce one JSON report, embedded Markdown, and a stable GUI model.
9. Mark the report `final` only when runtime status is `cleanup_verified`; for new `s4.runtime-evidence.v3`, Infrastructure Composer screenshot metadata must also be present. Otherwise keep it `interim` or `incomplete_artifacts`.

## Required report sections

- Candidate and official source.
- One-sentence conclusion.
- Skill 3 evaluation.
- PoC 成本估算報價單.
- 預估成本 vs 可歸因實際帳務成本.
- Skill 4 validation and runtime checks.
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
- If no attributable Cost Explorer, Billing, or CUR artifact is present, actual cost must remain `pending`.
- Do not omit zero-charge recipe resources, usage assumptions, exclusions or source URLs.
- `CREATE_COMPLETE` is deployment evidence, not cleanup evidence.
- Automated checks do not replace Console review.
- Console screenshot metadata proves only that a redacted PNG was captured, hashed, and shown through an approved channel. The program does not inspect image content; the named human confirmation carries that judgment.
- Sandbox evidence proves only the tested recipe and workload; do not generalize it to every environment.
- Missing evidence must remain `unknown`.

## Validation

```powershell
python -m unittest tests.test_s5 -v
```
