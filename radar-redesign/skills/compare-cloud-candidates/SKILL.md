---
name: compare-cloud-candidates
description: Convert a traceable Skill 1 artifact into evidence-based proposal cards and a comparison matrix without selecting a winner. Use when comparing cloud candidates, checking official documentation, Region or pricing evidence, exposing data gaps, or preparing a human shortlist for Skill 3.
---

# Skill 2 · Compare

Compare only candidates recorded by Skill 1. Prepare human decisions; do not make the shortlist or start evaluation automatically.

## Work from the project core

Run from `radar-redesign/`:

```powershell
python -m agentic_cloud_radar.cli s2 `
  --input .\out\s1.json `
  --output .\out\s2.json
```

Reuse `agentic_cloud_radar/s2.py`. Do not invent official URLs, pricing, company needs, or implementation claims.

## Workflow

1. Verify the input is an S1 artifact and preserve its `run_id`.
2. Re-fetch the candidate source and inspect candidate-relevant official links.
3. Build one proposal card per candidate with capabilities, delivery form, maturity, expected benefits, trade-offs, prerequisites, stop conditions, and evidence gaps.
4. Build a fixed comparison matrix so candidates use the same dimensions.
5. Mark Singapore availability only when candidate-specific official evidence supports it. Otherwise use `region_unknown`.
6. Treat pricing pages as evidence to review, not as a PoC cost estimate unless a usable amount is recorded.
7. Finish with `ready_for_human_shortlist`; ask a human to choose no more than three candidates.

## Evidence rules

- Use search results only to discover URLs; fetch and verify the page before citing it.
- Keep improvement statements as hypotheses unless the source contains measurable evidence.
- Do not select a champion without human input and company context.
- Do not let a Region warning block Skill 3; preserve it for the paid-PoC gate.

## Validation

```powershell
python -m unittest tests.test_s2 -v
```

Pass the S2 artifact and a human shortlist request to `$evaluate-cloud-candidate`.
