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

## Console Screenshot Gate

After deployment verification, use [`templates/console-review-agent-template.md`](./templates/console-review-agent-template.md). The agent must open the logged-in AWS Console, inspect the deployed stack's **Infrastructure Composer**, capture a screenshot, and show that image in the authenticated GUI or the active conversation. Do not start cleanup until a named human explicitly confirms after seeing the screenshot.

Screenshots are sensitive operational evidence: do not commit them or unredacted Console URLs. The review-evidence JSON stores only a reference, SHA-256, capture time, and whether it was shown through `gui` or `conversation`.

Commands:

```powershell
python -m agentic_cloud_radar.cli s4-deploy `
  --input .\out\s3.json `
  --approval .\out\s4-approval.json `
  --output .\out\s4-deployment-context.json `
  --runtime-output .\out\s4-runtime.json `
  --execute

python -m agentic_cloud_radar.cli s4-console-review-packet `
  --input .\out\s4-runtime.json `
  --output .\out\s4-console-review-packet.json

node .\scripts\s4-capture-infrastructure-composer.mjs `
  --runtime .\out\s4-runtime.json `
  --packet .\out\s4-console-review-packet.json `
  --output-dir .\out\s4-console-review\<run-id> `
  --evidence-output .\out\s4-console-review\<run-id>\s4-console-review-evidence.json `
  --shared-via conversation

# Show the generated PNG in the GUI or active conversation, obtain human confirmation, then:
python -m agentic_cloud_radar.cli s4-close `
  --input .\out\s4-runtime.json `
  --review-evidence .\out\s4-console-review\<run-id>\s4-console-review-evidence.json `
  --confirmed-by "<named-human>" `
  --notes "<concise-review-note>" `
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
7. Run the Playwright capture command from the Console review packet. It opens a headful browser, uses an existing or newly authenticated AWS Console session, navigates to CloudFormation / Infrastructure Composer, captures the canvas PNG, and writes local evidence JSON.
8. Pause for explicit named-human cleanup confirmation. Do not infer confirmation from a prior deployment approval.
9. Run `s4-close --execute`; it records screenshot evidence, cleans only the reviewed run, and re-queries the scoped resources.
10. Produce Skill 5's actual-PoC conclusion only from the resulting `cleanup_verified` runtime artifact.

## Registered recipes

- S3 Files with EC2 mount and bidirectional object checks.
- Lambda self-managed S3 code storage with versioned artifact, `REFERENCE` mode, and invoke verification.

Unknown candidates must stop at `needs_poc_recipe`.

The fixed sandbox ceiling is a policy control, not a quotation. Do not substitute it for missing rates.

## Playwright setup

If the workspace does not already have Playwright available, install it locally before the Console review step:

```powershell
npm install --save-dev playwright
npx playwright install chromium
```

The Playwright script may pause for manual AWS login in the visible browser. Screenshot files and browser profile data stay in ignored local folders and must not be committed.

## Validation

```powershell
python -m unittest tests.test_s3_s4 -v
```

Pass S4 validation and optional runtime evidence to `$report-cloud-evidence`.
