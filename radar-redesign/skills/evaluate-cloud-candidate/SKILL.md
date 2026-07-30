---
name: evaluate-cloud-candidate
description: Evaluate human-shortlisted cloud candidates from a Skill 2 artifact with the fixed Skill 3 rubric and explicit evidence limits. Use after a person selects up to three candidates and needs a reproducible score, confidence level, risk analysis, or recommendation for low-risk validation or controlled PoC review.
---

# Skill 3 · Evaluate

Evaluate only a human shortlist. Do not silently select candidates or reinterpret missing context as facts.

## Inputs

- S2 comparison artifact with a stable `run_id`.
- Human shortlist request naming no more than three S2 candidate IDs.
- Optional `problem_to_solve`, `available_environment`, and `forbidden_data_and_permissions`.

Omitted optional context remains a data gap. Human candidate selection is mandatory.

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
4. Record weighted score, confidence, Region state, governance flags, cost state, stop conditions, and evidence limits.
5. Set `recommend_low_risk_validation` from technical value, confidence, and hard blockers.
6. Set `eligible_for_paid_poc_review` separately from business context, environment, forbidden boundaries, governance flags, and Region evidence.
7. Keep legacy `recommend_s4` mapped only to low-risk validation for v1 consumer compatibility; never treat it as deployment eligibility.

## Guardrails

- Do not award points from an unverified static case study.
- Do not convert `region_unknown` into unavailable or available.
- Do not call a human-approved spending ceiling an official estimate.
- Do not describe a rubric fallback as an LLM or external API result.
- Missing optional context may block paid-PoC review, but must not by itself block document, local, or other low-risk validation.

## Validation

```powershell
python -m unittest tests.test_s3_s4.S3S4Tests.test_s3_stops_without_human_shortlist -v
python -m unittest tests.test_s3_s4.S3S4Tests.test_s3_evaluates_shortlisted_candidate_without_region_blocking_s3 -v
```

Pass the S3 artifact to `$validate-cloud-poc`.
