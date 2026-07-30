---
name: validate-cloud-poc
description: Validate an evaluated cloud candidate with low-risk checks or a tightly controlled AWS PoC while preserving artifact lineage and human gates. Use for Skill 4 validation, CDK or CloudFormation review, named-human approval, cost ceilings, runtime evidence, Console review, or run-scoped cleanup.
---

# Skill 4 · Validate

Default to low-risk validation. Never create paid AWS resources through the normal `s4` command.

Read Skill 3 decisions independently:

- `recommend_low_risk_validation` controls document, local, schema, template, or validator work.
- `eligible_for_paid_poc_review` controls entry to the separate paid-PoC approval gate.
- Legacy `recommend_s4` is only a compatibility alias for low-risk validation.

## Low-risk validation

From `radar-redesign/`:

```powershell
python -m agentic_cloud_radar.cli s4 `
  --input .\out\s3.json `
  --output .\out\s4.json
```

Use this path for document, schema, template, or local checks. State `cloud_resources_created=false` when no resources were created.

## Controlled PoC

Read `docs/s4-完整PoC部署操作.md` before any live action.

Require all of the following:

- Matching S1/S2/S3 lineage and artifact hashes.
- Skill 3 `eligible_for_paid_poc_review=true`, unless a recorded Region warning is explicitly acknowledged without any other governance or context gap.
- A registered candidate-specific recipe.
- Named human approval and `deployment_authorized=true`.
- Target Region, success criteria, cost ceiling, permissions, forbidden data, and cleanup scope.
- A second explicit CLI `--execute`.

Commands:

```powershell
python -m agentic_cloud_radar.cli s4-deploy `
  --input .\out\s3.json `
  --approval .\out\s4-approval.json `
  --output .\out\s4-deployment-context.json `
  --runtime-output .\out\s4-runtime.json `
  --execute

python -m agentic_cloud_radar.cli s4-console-review `
  --input .\out\s4-runtime.json `
  --confirmed-by "<named-human>" `
  --notes "<concise-review-note>" `
  --output .\out\s4-runtime-reviewed.json

python -m agentic_cloud_radar.cli s4-cleanup `
  --input .\out\s4-runtime-reviewed.json `
  --output .\out\s4-runtime-cleaned.json `
  --execute
```

## Workflow

1. Validate lineage and approval before contacting AWS.
2. Synthesize the candidate recipe and inspect CloudFormation.
3. Create only run-derived resources in the approved intern non-production scope.
4. Record deployment status and runtime checks without secrets, account IDs, full ARNs, or private addresses.
5. Pause for the named human to inspect CloudFormation and service-specific Console pages.
6. Run cleanup only after confirmed review and only for the reviewed run.
7. Re-query stack, bucket, compute, and candidate-specific resources; mark cleanup verified only from evidence.

## Registered recipes

- S3 Files with EC2 mount and bidirectional object checks.
- Lambda self-managed S3 code storage with versioned artifact, `REFERENCE` mode, and invoke verification.

Unknown candidates must stop at `needs_poc_recipe`.

## Validation

```powershell
python -m unittest tests.test_s3_s4 -v
```

Pass S4 validation and optional runtime evidence to `$report-cloud-evidence`.
