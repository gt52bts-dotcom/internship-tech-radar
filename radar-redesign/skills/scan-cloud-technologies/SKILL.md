---
name: scan-cloud-technologies
description: Scan trusted public AWS and open-source sources, remove irrelevant material, and produce a traceable Skill 1 candidate artifact. Use for direct AWS/GitHub/GitLab/Codeberg URL intake, AWS technology landscape discovery, GA-evidence screening, source cleaning, or candidate-list creation before comparison.
---

# Skill 1 · Scan

Create a source-bound S1 artifact. Do not rank candidates, evaluate business fit, or start a PoC.

## Run directory convention

Keep every artifact for one evaluation in the same dedicated folder, for example `./out/run/`. Skill 1 mints the immutable `run_id`; later stages must preserve it and keep their outputs beside the S1 artifact. Do not combine artifacts from different runs in one folder.

## Work from the project core

Run commands from `radar-redesign/`. Reuse `agentic_cloud_radar/s1.py` through the CLI; do not duplicate its scanning logic inside this skill.

Direct URL:

```powershell
python -m agentic_cloud_radar.cli s1-url `
  --url "<trusted-public-url>" `
  --output .\out\run\s1.json
```

Discovery:

```powershell
python -m agentic_cloud_radar.cli s1 `
  --input .\samples\landscape-ga-singapore-request.json `
  --output .\out\run\s1.json
```

## Workflow

1. Choose `s1-url` when a human supplies one public candidate URL. Choose `s1` for landscape or focused discovery.
2. Accept only trusted public HTTPS sources supported by the core.
3. Preserve source URL, fetch status, timestamps, maturity evidence, detected services, and data gaps.
4. Remove marketing or irrelevant text only when the remaining candidate and evidence stay traceable.
5. Treat missing GA, Region, pricing, or service evidence as a gap. Do not infer preview, availability, or cost.
6. Return the S1 artifact path and summarize candidate count, excluded material, fetch failures, and gaps.

## Stop conditions

- Stop on invalid input before making external requests.
- Do not turn GitHub metadata into AWS GA evidence.
- Do not claim an annual archive is complete when RSS only exposes recent entries.
- Do not drop a candidate merely because an official Region statement is missing; preserve it as a review gap for Skill 2 and the controlled deployment gate.
- Exclude Bedrock recommendations unless the human explicitly changes the project constraint.

## Validation

Run:

```powershell
python -m unittest tests.test_s1 -v
```

Pass the resulting S1 artifact to `$compare-cloud-candidates`.
