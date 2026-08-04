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
7. Populate `poc_decision_gate` with every evaluated option, including score, quote status, low/expected/high estimate, recommended approval ceiling, blocker list, and the required human outputs: `selected_candidate_id`, `approved_by`, `approved_ceiling_usd`.
8. When writing the optional Skill 3 PoC decision report, explain the article before the approval decision: what changed, why it matters, key source-backed points, and the inferred minimal implementation architecture. Then show PoC threshold, score, quote, recipe, blockers, and what Cleo must approve before Skill 4.
9. Keep Region and pricing uncertainty in `poc_review_notes`; do not require the user to configure an environment.
10. `recommend_s4` is an input-only compatibility fallback for old artifacts. New S3 artifacts do not produce low-risk or separate paid-PoC decision fields.

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

Required human outputs: `selected_candidate_id`, `approved_by`, `approved_ceiling_usd`. Technical eligibility is never approval.

## Cost scope

The quote is a pre-deployment public-rate-card estimate. This pipeline does not collect actual AWS billing and never reconciles estimate against invoice, so the billing method and formula for every line item must be correct on their own: monthly-rate resources prorated by PoC hours, request-priced resources by request count, Lambda charged only per invocation plus GB-seconds. Do not omit any resource the recipe creates, including default CloudWatch log groups.

Pass the S3 artifact to `$validate-cloud-poc`.
