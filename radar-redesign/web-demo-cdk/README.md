# AWS Web Demo Deployment

This CDK app deploys an AWS-hosted, artifact-first web demo for S1 Scan through Skill 5 Report.

## What It Creates

- Private, encrypted, versioned S3 bucket for run artifacts with a 30-day lifecycle.
- Python Lambda that runs the same S1, S2, Skill 3, S4 validator, and Skill 5 report renderer as the CLI.
- API Gateway REST API with a low request throttle.
- Private static-site S3 bucket fronted by CloudFront.

The web API intentionally does not create PoC resources. A full S4 PoC still uses the same repository's explicit `s4-deploy --execute` runner after a named human approval and artifact-lineage checks. This prevents a browser action from bypassing the approval, cost ceiling, Console review, or cleanup gates.

## Deploy

```powershell
cd .\web-demo-cdk
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
aws sts get-caller-identity --profile intern
npx cdk bootstrap --profile intern
npx cdk deploy --profile intern
```

CDK prints `WebsiteUrl`, `ApiUrl`, and the artifact bucket name when deployment completes. It is deliberately not deployed by this repository command automatically.

## API Contract

| Method | Route | Result |
| --- | --- | --- |
| POST | `/runs/url` | Runs S1 URL import and S2 compare. |
| POST | `/runs/discovery` | Runs S1 discovery and S2 compare. |
| POST | `/runs/{run_id}/shortlist` | Runs Skill 3 after human shortlist context. |
| POST | `/runs/{run_id}/validate` | Builds an S4 PoC approval-gate artifact only; it never deploys resources. |
| POST | `/runs/{run_id}/report` | Builds an S5 JSON, Markdown, and GUI model report. |
| GET | `/runs/{run_id}/artifacts/{stage}` | Reads an artifact, for example `s1`, `s2`, `s3`, `s4`, or `s5`. |

## Before Sharing Beyond a Demo

The current demo API is public so the intern account can try the web flow without an identity setup. Keep the API URL private, and add Cognito or an equivalent company identity control before sharing it broadly. The API has no S4 deployment capability and is throttled, but public access still consumes Lambda and API Gateway usage.
