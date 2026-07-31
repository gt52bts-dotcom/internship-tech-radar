---
name: evaluate-cloud-candidate
description: Evaluate one human-selected cloud candidate from a Skill 2 artifact with the fixed Skill 3 public-evidence rubric and produce an auditable full-PoC cost quotation for a registered recipe. Use after a person selects one candidate and needs a reproducible score, confidence level, risk analysis, cost estimate, and technical eligibility for a controlled Skill 4 PoC.
---

# Skill 3 · Evaluate

Evaluate only one human-selected candidate. Do not silently select candidates or require custom environment forms.

## Inputs

- S2 comparison artifact with a stable `run_id`.
- Human selection request naming exactly one S2 candidate ID.

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
2. Stop with `needs_human_shortlist` when no human selection exists or more than one candidate is selected.
3. Score only evidence-supported dimensions with the fixed rubric.
4. Record weighted score, confidence, Region state, governance flags, stop conditions, and evidence limits.
5. For the selected candidate, create the entire PoC quote before Skill 4: low/expected/high usage, itemized rates, formulas, official sources, validity, exclusions, and a recommended approval ceiling. An unknown recipe must return `needs_registered_cost_model`, never an invented amount.
6. Set the one decision field, `recommend_poc`, only when the score is `>= 3.75` on the 5-point weighted rubric, confidence is at least `medium`, no PoC blocker exists, and the quote status is `estimated`. Treat this field as technical eligibility for a controlled PoC, not proof of workload fit.
7. Keep Region and pricing uncertainty in `poc_review_notes`; do not require the user to configure an environment.
8. `recommend_s4` is an input-only compatibility fallback for old artifacts. New S3 artifacts do not produce low-risk or separate paid-PoC decision fields.

## Guardrails

- Confidence enum is ordered `low < medium < high`; only `medium` and `high` can pass the PoC eligibility gate.
- PoC blocker codes are concrete stop conditions such as `not_ga`, `no_public_source`, `forbidden_service`, `no_registered_cost_model`, `no_registered_poc_recipe`, `target_region_unavailable`, `unsafe_permissions`, or `production_data_required`.
- Cost model and deployment recipe registration must be paired. A candidate must not be PoC-eligible if Skill 3 has a cost model but Skill 4 has no matching recipe.
- Do not award points from an unverified static case study.
- Do not convert `region_unknown` into unavailable or available.
- Do not call a human-approved spending ceiling an official estimate.
- Do not call a public-price estimate an AWS invoice, tax invoice or binding sales quote.
- Keep cost outside the technical rubric score.
- Do not describe a rubric fallback as an LLM or external API result.
- Do not infer workload fit from public evidence; report it as not assessed.

## Validation

```powershell
python -m unittest tests.test_s3_s4 -v
```

Pass the S3 artifact to `$validate-cloud-poc`.
