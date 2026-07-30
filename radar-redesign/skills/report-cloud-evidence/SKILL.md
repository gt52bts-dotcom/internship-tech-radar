---
name: report-cloud-evidence
description: Render S1 through S4 artifacts and optional runtime evidence into traceable JSON, Markdown, and GUI report models without adding unsupported claims. Use for Skill 5 interim or final technical reports, evidence ledgers, verified-versus-unknown summaries, artifact lineage checks, or presentation-ready report data.
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
  --runtime .\out\s4-runtime.json `
  --output .\out\s5-report.json `
  --markdown-output .\out\s5-report.md
```

Reuse `agentic_cloud_radar/s5.py`.

## Workflow

1. Check stage presence, `run_id`, and candidate lineage.
2. Mark mismatched or missing required artifacts as `incomplete_artifacts`.
3. Summarize the Skill 3 score and confidence without recalculation.
4. Separate verified facts from unknown or unverified statements.
5. Build an evidence ledger linking claims to source or runtime artifacts.
6. Produce one JSON report, embedded Markdown, and a stable GUI model.
7. Mark the report `final` only when runtime status is `cleanup_verified`; otherwise keep it `interim`.

## Required report sections

- Candidate and official source.
- One-sentence conclusion.
- Skill 3 evaluation.
- Skill 4 validation and runtime checks.
- Verified facts.
- Unknown or insufficiently supported claims.
- Next reminders.
- Evidence ledger and S1-S4 funnel.

## Claim rules

- A named-human cost ceiling is not an official price.
- `CREATE_COMPLETE` is deployment evidence, not cleanup evidence.
- Automated checks do not replace Console review.
- Intern non-production evidence does not prove company-environment fitness.
- Missing evidence must remain `unknown`.

## Validation

```powershell
python -m unittest tests.test_s5 -v
```
