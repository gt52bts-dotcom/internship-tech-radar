# Reference Runs For Cross-Computer Continuity

This folder contains curated S1-S5 artifacts that are safe to keep in Git for
project handoff and cross-computer continuity. They are copied from local
`radar-redesign/out/` runs and redacted before commit.

Included runs:

- `connect-customer-data-lake-20260731`: interim single-candidate run with
  Skill 3 generic quote and no AWS resource creation.
- `lambda-self-managed-code-storage-20260731`: completed Skill 1 through
  Skill 5 PoC run for Lambda self-managed S3 code storage.
- `s3-files-20260731-manual-console`: completed Skill 1 through Skill 5 PoC
  run for S3 Files, including cleanup-before usage snapshot.

Redaction rules applied:

- AWS account IDs are replaced with `<aws-account-id-redacted>`.
- AWS ARNs are replaced with `<aws-arn-redacted>`.
- AWS Console URLs are replaced with `<aws-console-url-redacted>`.
- Local absolute workspace paths are replaced with `<local-workspace-redacted>`.

Do not commit raw `radar-redesign/out/`, Console screenshots, unredacted Console
URLs, AWS credentials, `.env` files, CDK generated `cdk.out/`, or local runtime
profiles. These reference artifacts are for review and reproducibility; rerun
the CLI from the committed core when fresh artifacts are needed.
