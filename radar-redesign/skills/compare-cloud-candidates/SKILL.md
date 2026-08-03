---
name: compare-cloud-candidates
description: Convert a traceable Skill 1 artifact into evidence-based proposal cards and a comparison matrix without selecting a winner. Use when comparing cloud candidates, checking official documentation, Region or pricing evidence, exposing data gaps, or preparing one human candidate selection for Skill 3.
---

# Skill 2 · Compare

Compare only candidates recorded by Skill 1. Prepare the human decision; do not select a candidate or start evaluation automatically.

## Work from the project core

Run from `radar-redesign/`:

```powershell
python -m agentic_cloud_radar.cli s2 `
  --input .\out\run\s1.json `
  --output .\out\run\s2.json
```

Reuse `agentic_cloud_radar/s2.py`. Do not invent official URLs, pricing, workload needs, or implementation claims.

## Workflow

1. Verify the input is an S1 artifact and preserve its `run_id`.
2. Re-fetch the candidate source and inspect candidate-relevant official links.
3. Build one proposal card per candidate with capabilities, delivery form, maturity, expected benefits, trade-offs, prerequisites, stop conditions, and evidence gaps.
4. Build a fixed comparison matrix so candidates use the same dimensions.
5. Mark Singapore availability only when candidate-specific official evidence supports it. Otherwise use `region_unknown`.
6. Treat pricing pages as evidence to review, not as a PoC cost estimate unless a usable amount is recorded.
7. Finish with `ready_for_human_shortlist`; hand every candidate to Skill 3. Skill 2 does not ask for a selection: the single merged gate after Skill 3 picks the candidate and approves the PoC at the same time, so value and estimated cost are seen together. The historical field name `shortlist` remains only for CLI and schema compatibility.

## Evidence rules

- Use search results only to discover URLs; fetch and verify the page before citing it.
- Keep improvement statements as hypotheses unless the source contains measurable evidence.
- Do not select a champion without human input.
- Keep Region and pricing gaps as review notes; do not turn them into extra user forms.

## Validation

```powershell
python -m unittest tests.test_s2 -v
```

Pass the S2 artifact and the one-candidate human selection request to `$evaluate-cloud-candidate`.
