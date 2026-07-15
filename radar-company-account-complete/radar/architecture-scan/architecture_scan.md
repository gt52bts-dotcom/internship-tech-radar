# AWS Architecture Scout Report

- Package: `Cathay Tech Intel Pipeline v3`
- Variant: company-account landing version
- Region: `ap-southeast-1`
- Review date: 2026-07-14
- Verdict: **deployable landing package**

## Summary

This package is no longer just a CDK skeleton. It includes deployable CDK stacks, Lambda runtime code, data fixtures, case studies, quote gate, cost documents, Step Functions orchestration, and company-account deployment instructions.

CloudFront and Amazon Bedrock are intentionally excluded from this variant. The company account is expected to be region-restricted, so reports are stored in S3 and exposed through S3 object retrieval / presigned URLs instead of a CloudFront distribution.

## Coverage

| Block | Status | Evidence |
|---|---|---|
| Single AWS radar workflow | Implemented | `cdk/lambda_src/s1_scan.py` to `s5_report.py`; no Entry B path |
| Quote gate before LLM | Implemented | `s2b_quote.py`, `pipeline_stack.py`, `pipeline_lib.py` |
| Five-step final scoring | Implemented | S1/S2/S2b/S3/S4/S5 in Step Functions |
| S3 persistence | Implemented | `data_stack.py`, `common.py`, `s5_report.py` |
| DynamoDB pick log | Implemented | `data_stack.py`, `log_pick`, `record_human_pick.py` |
| Secrets Manager key storage | Implemented | `secrets_stack.py`, `common.py` |
| Anthropic API with fallback | Implemented | `s3_evaluate.py`, `s4_validate.py`, `common.py` |
| EventBridge scheduled ingestion | Implemented, default disabled | `pipeline_stack.py` |
| Cognito + API Gateway | Implemented, optional | `pipeline_stack.py`, `api_start.py`, `-c enable_api=true` |
| CloudWatch logging | Implemented | Explicit Lambda and Step Functions log groups |
| CloudFront | Intentionally excluded | Company-account global-service risk; S3 presigned URL used instead |
| Bedrock / Knowledge Bases | Intentionally excluded | Company-account SCP, model enablement, and cost-control risk |
| CDK synthesis | Verified | `cdk synth` succeeded on 2026-07-14 |

## Improvements Made For Landing Version

- Added formal quote document: `docs/v3-技術雷達-報價單.md`.
- Aligned `README.md`, `DEPLOY.md`, `cost-quotation.md`, and `cost-estimate.yaml` with company-account deployment.
- Fixed Step Functions `run_id` behavior: manual `run_id` is preserved; missing `run_id` gets generated automatically.
- Removed stale CloudFront/demo wording from deployment docs.
- Added CDK context flag for stable cross-stack reference behavior.
- Verified Python syntax with `compileall`.
- Verified CDK synthesis with `cdk synth`.

## Remaining External Requirements

These are not code gaps; they must be provided by the company AWS environment:

- AWS credentials for the company account.
- CDK bootstrap permission, or mentor/admin assistance to bootstrap once.
- Anthropic API key stored in Secrets Manager.
- Approval to enable optional API Gateway/Cognito or EventBridge schedule if needed.

## Deployment Readiness

Ready for company-account deployment validation:

```powershell
cd cdk
.\scripts\build-layer.ps1 -Python python
cdk synth
cdk deploy cathay-techintel-v3-data cathay-techintel-v3-secrets cathay-techintel-v3-pipeline
```
