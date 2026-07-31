---
name: validate-cloud-poc
description: Execute the single controlled AWS PoC stage after Skill 3 has produced a complete estimate, while preserving artifact lineage and a short human gate. Use for Skill 4 quote-versus-ceiling checks, CDK or CloudFormation deployment, named-human approval, runtime evidence, Console review, or run-scoped cleanup.
---

# Skill 4 · Validate

Skill 4 means one thing: a controlled PoC that creates bounded AWS resources. It never starts automatically, but it is not a second, low-risk validation track.

## PoC gate

From `radar-redesign/`:

```powershell
python -m agentic_cloud_radar.cli s4 `
  --input .\out\s3.json `
  --output .\out\s4.json
```

This command creates the approval gate artifact only. With no approval it returns `awaiting_poc_approval`; it does not redefine Skill 4 as a no-cost validation.

## Controlled PoC

Read `docs/s4-完整PoC部署操作.md` before any live action.

Require all of the following:

- Matching S1/S2/S3 lineage and artifact hashes.
- Skill 3 `recommend_poc=true`.
- A registered candidate-specific recipe and its complete S3 quotation.
- The quote's high-use estimate must stay within the approved sandbox ceiling.
- Named human approval and `deployment_authorized=true`.
- A second explicit CLI `--execute`.

Use the built-in small-cost ceiling, target Region, recipe success criteria, and cleanup scope unless the reviewer supplies a stricter override.

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

1. Validate lineage, quote status, estimated range, validity and approval before contacting AWS.
2. Synthesize the candidate recipe and inspect CloudFormation.
3. Create only run-derived sandbox resources.
4. If the same run-derived stack is already `CREATE_COMPLETE`, resume its verification instead of creating duplicate resources.
5. Treat candidate-service propagation as eventually consistent: use a bounded retry for expected transient read-back gaps, and fail after the timeout.
6. Record deployment status and runtime checks without secrets, account IDs, full ARNs, or private addresses.
7. Pause for the named human to inspect CloudFormation and service-specific Console pages.
8. Run cleanup only after confirmed review and only for the reviewed run.
9. Re-query stack, bucket, compute, and candidate-specific resources; mark cleanup verified only from evidence.

## Registered recipes

- S3 Files with EC2 mount and bidirectional object checks.
- Lambda self-managed S3 code storage with versioned artifact, `REFERENCE` mode, and invoke verification.

Unknown candidates must stop at `needs_poc_recipe`.

The fixed sandbox ceiling is a policy control, not a quotation. Do not substitute it for missing rates.

## Validation

```powershell
python -m unittest tests.test_s3_s4 -v
```

Pass S4 validation and optional runtime evidence to `$report-cloud-evidence`.
