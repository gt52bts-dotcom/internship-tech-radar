# Cross-Computer Migration Status

Last updated: 2026-08-03 Asia/Taipei.

Latest pushed checkpoint: `45141e6 Record Lambda cleanup and S5 final`.

## What Is In GitHub

The repository is the source of truth for continuing work on another computer.
Clone the repository and continue from `main`:

```powershell
git clone https://github.com/gt52bts-dotcom/internship-tech-radar.git
```

The current GitHub version includes:

- Project memory, AI PM inbox, daily logs, README, final proposal drafts, and
  work-log templates.
- The current `radar-redesign/` Skill 1 through Skill 5 core, tests, Skill
  packages, and Claude GUI handoff package.
- Curated redacted reference artifacts under `radar-redesign/reference-runs/`.
- Historical research evidence under `research/` and selected small PoC
  evidence under `poc/`.
- The current AI PM meeting deck under `outputs/`.

## Current Workflow Decisions To Preserve

- Skill 3 is the main human decision point: by the end of S3 the report should
  already explain the news, show its value, provide a public-rate-card PoC quote,
  and include a human-readable architecture image.
- Human-facing Skill 3 decision reports should be HTML by default and include a
  GPT-style raster PNG architecture infographic embedded as a data URI, not only
  a Mermaid/text flowchart and not a Markdown image link.
- Skill 4 PoC is not mainly for proving business value or one-month actual cost.
  Its value is proving deployment feasibility, Region/account compatibility,
  IAM/resource wiring, runtime verification, Console review, pre-cleanup usage
  snapshot capture, and safe cleanup.
- Skill 5 should report the evidence chain and limits. It should not turn short
  runtime usage facts into AWS Billing/Cost Explorer/CUR actual cost.

## What Is Intentionally Not In GitHub

The following local-only categories should not be required on a new computer:

- Raw `radar-redesign/out/` runtime dumps.
- Generated local stage packages such as
  `lambda-stage-artifacts-20260803-150444.zip`.
- Console screenshots and unredacted Console URLs.
- CDK generated output such as `cdk.out/`, generated zips, local build caches,
  dependency folders, and `.local/` runtime folders.
- Old abandoned implementation copies such as the former company-account /
  `cathay-techintel-v3` tree.
- Credentials, `.env` files, private keys, AWS profiles, and local browser
  session data.

## How To Continue

1. Clone the repository.
2. Read `PROJECT_MEMORY.md` and the latest daily log before making decisions.
3. Use `radar-redesign/` as the active implementation.
4. Use `radar-redesign/reference-runs/` for evidence examples, not raw local
   runtime output.
5. Regenerate local artifacts through the CLI when needed.
6. For a new Skill 3 decision report, generate the PNG first, then produce the
   self-contained HTML review artifact locally before asking for human PoC
   approval.
