---
name: evaluate-cloud-candidate
description: Evaluate human-shortlisted cloud candidates from a Skill 2 artifact with the fixed Skill 3 public-evidence rubric and produce an auditable full-PoC cost quotation for each registered recipe. Use after a person selects up to three candidates and needs a reproducible score, confidence level, risk analysis, cost estimate, and one recommendation for a controlled Skill 4 PoC.
---

# Skill 3 · Evaluate

Evaluate only a human shortlist. Do not silently select candidates or require custom environment forms.

## Inputs

- S2 comparison artifact with a stable `run_id`.
- Human shortlist request naming no more than three S2 candidate IDs.

Human candidate selection is mandatory. Public-evidence evaluation does not require a business problem, environment description, or data-boundary form.

## Run

From `radar-redesign/`:

```powershell
python -m agentic_cloud_radar.cli s3 `
  --input .\out\s2.json `
  --shortlist .\out\shortlist.json `
  --output .\out\s3.json
```

Reuse the fixed rubric in `agentic_cloud_radar/s3.py`.

## Workflow

1. Verify S2 lineage and shortlist candidate IDs.
2. Stop with `needs_human_shortlist` when no human selection exists.
3. Score only evidence-supported dimensions with the fixed rubric.
4. Record weighted score, confidence, Region state, governance flags, stop conditions, and evidence limits.
5. For every selected candidate, create the entire PoC quote before Skill 4: low/expected/high usage, itemized rates, formulas, official sources, validity, exclusions, and a recommended approval ceiling. An unknown recipe must return `needs_registered_cost_model`, never an invented amount.
6. Set the one decision field, `recommend_poc`, only when the score reaches 3.75, confidence is at least medium, no PoC blocker exists, and the quote status is `estimated`.
7. Keep Region and pricing uncertainty in `poc_review_notes`; do not require the user to configure an environment.
8. `recommend_s4` is an input-only compatibility fallback for old artifacts. New S3 artifacts do not produce low-risk or separate paid-PoC decision fields.

## Guardrails

- Do not award points from an unverified static case study.
- Do not convert `region_unknown` into unavailable or available.
- Do not call a human-approved spending ceiling an official estimate.
- Do not call a public-price estimate an AWS invoice, tax invoice or binding sales quote.
- Keep cost outside the technical rubric score.
- Do not describe a rubric fallback as an LLM or external API result.
- Do not infer workload fit from public evidence; report it as not assessed.

## Validation

```powershell
python -m unittest tests.test_s3_s4.S3S4Tests.test_s3_stops_without_human_shortlist -v
python -m unittest tests.test_s3_s4.S3S4Tests.test_s3_evaluates_shortlisted_candidate_without_region_blocking_s3 -v
```

Pass the S3 artifact to `$validate-cloud-poc`.
