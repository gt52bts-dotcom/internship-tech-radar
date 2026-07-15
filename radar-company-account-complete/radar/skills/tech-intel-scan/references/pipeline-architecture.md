# Pipeline Architecture Reference

Read this file when you need to explain or modify the Cathay Tech Intel v3 architecture.

## Core Decision

v3 separates the system into three layers:

- Skills are the AI operating playbook for local Claude/Codex usage.
- CDK is the AWS deployment skeleton and runtime wiring.
- Anthropic API is the model provider, stored through AWS Secrets Manager instead of Bedrock model access.

## Revised Single-Entry Radar Flow

There is only one entry path:

1. Gather AWS concepts from RSS or packaged fixtures.
2. Run L0 deterministic cleanup: remove duplicates, irrelevant items, Preview/Beta items, and non-AWS radar topics.
3. Run L1 ranking against Cathay needs.
4. Run L2 evaluation on every surviving candidate.
5. Run independent validation on every evaluated candidate.
6. Select the final Top 3 only after evaluator and validator scores are averaged.
7. Put GCP/Azure equivalent-service comparison only in the final technical report.

Do not reintroduce a second cross-cloud scouting path. Cross-cloud comparison is report context only.

## AWS Deployment Mapping

- EventBridge Scheduler starts the daily run at 08:00 Asia/Taipei.
- Step Functions orchestrates S1 through S5.
- Lambda S1 scans RSS or fixtures and writes `runs/<run_id>/s1_scan.json`.
- Lambda S2 ranks candidates and writes `s2_compare.json`.
- Lambda S3 evaluates every L1 survivor with Anthropic API when configured, then rubric fallback.
- Lambda S4 independently validates every evaluated item.
- Lambda S5 calculates final average scores, writes `s5_report.json`, `report.html`, and `reports/latest.html`.
- S3 stores run artifacts and final HTML reports.
- CloudFront serves the latest report over HTTPS.
- DynamoDB stores future human pick/experiment tracking records.
- Secrets Manager stores the Anthropic API key.
- KMS encrypts S3 and DynamoDB data.

## Report Requirements

The final report must include:

- Final Top 3 concepts selected by average score.
- Source URL and evidence summary.
- Cathay application scenario.
- Enterprise case evidence.
- Risk or governance flags.
- GCP/Azure equivalent-service comparison.
- Full system scoring table.

## Deployment Safety

The first AWS deployment can run without a real Anthropic key because S3/S4 fall back to deterministic rubric scoring. Replace the Secrets Manager value before production-style runs.
