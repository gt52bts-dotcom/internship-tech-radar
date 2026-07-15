# v3 Tech Radar Quotation

Date: 2026-07-14  
Project: Cathay Tech Intel Pipeline v3  
Region: AWS ap-southeast-1  
Purpose: company-account landing validation with a per-run quote gate before LLM evaluation.

## Basis

The 2026-07-13 version already completed an end-to-end v3 AWS pipeline run. This package adds a formal quote gate and quotation outputs so the company-account deployment can be validated with cost control.

## Included Quote-Gate Scope

- `s2b_quote.py` runs after S2 and before S3/S4 LLM evaluation.
- Each execution writes `quotation.json` and `quotation.html`.
- If the quote is within `MAX_RUN_USD`, the pipeline proceeds with LLM evaluation.
- If the quote exceeds `MAX_RUN_USD`, the pipeline falls back to zero-token rubric mode.
- S5 keeps quoted vs actual LLM cost fields for later calibration.

## Per-Run Quote

Default assumptions:

- Candidate count after S2: 6
- Evaluator model: Claude Sonnet 4.5
- Validator model: Claude Haiku 4.5
- Per-run cap: USD 0.50
- AWS fixed allocation: USD 0.01 / run

| Line Item | Model | Estimated Tokens | Price | Estimated Cost |
|---|---|---:|---:|---:|
| S3 Evaluator | Claude Sonnet 4.5 | 9,000 input / 2,400 output | USD 3 / 15 per MTok | USD 0.0630 |
| S4 Validator | Claude Haiku 4.5 | 7,200 input / 1,800 output | USD 1 / 5 per MTok | USD 0.0162 |
| AWS fixed allocation | Lambda / Step Functions / S3 / DynamoDB | - | - | USD 0.0100 |
| **Total** | - | - | - | **USD 0.0892** |

Decision: **approve** because USD 0.0892 <= USD 0.50.

## Monthly Landing-Validation Estimate

| Service | Purpose | Monthly Estimate |
|---|---|---:|
| S3 | Pipeline JSON, HTML reports, and quotation files | < USD 1 |
| Lambda | S1-S5 and quote gate | < USD 1 |
| Step Functions | Quote-gated workflow orchestration | < USD 1 |
| DynamoDB | AI / human pick logs | < USD 1 |
| Secrets Manager | Anthropic API key | ~ USD 0.40 |
| CloudWatch Logs | Logs and troubleshooting | USD 1-3 |
| EventBridge Scheduler | Daily schedule, disabled by default | ~ USD 0 |
| API Gateway / Cognito | Optional manual trigger API | < USD 1 |
| Anthropic API | Usage-based model calls | ~ USD 0.09 / approved run |

Expected light-use monthly total: **USD 5-15**.  
Implementation / validation budget cap: **USD 100**.

## Cost-Control Decisions

- Amazon Bedrock is excluded.
- CloudFront is excluded for the company-account package to avoid global-service restrictions.
- OpenSearch, RDS, EC2, and Bedrock Knowledge Bases are excluded.
- Anthropic API key is stored in Secrets Manager.
- EventBridge schedule is disabled by default.
- Over-budget runs fall back to zero-token rubric mode.

## Runtime Outputs

```text
s3://<bucket>/runs/<run_id>/quotation.json
s3://<bucket>/runs/<run_id>/quotation.html
s3://<bucket>/runs/<run_id>/report.html
s3://<bucket>/runs/<run_id>/cost-estimate.yaml
s3://<bucket>/reports/latest.html
s3://<bucket>/reports/cost-estimate.yaml
```

## Conclusion

The company-account landing package is ready for controlled deployment validation. The default full LLM run is quoted at approximately **USD 0.0892**, below the **USD 0.50** per-run cap.
