# Cathay Tech Intel v3 Cost Quotation

## Scope

This quotation covers the company-account landing version of Cathay Tech Intel Pipeline v3 in AWS `ap-southeast-1`.

The package includes deployable CDK stacks, Lambda handlers, Step Functions orchestration, S3 report storage, DynamoDB pick logs, Secrets Manager, quote gate, cost documents, and local Skills.

## Budget

Implementation / landing validation budget cap: **USD 100**.

## Cost Strategy

- Do not use Amazon Bedrock in this phase.
- Do not use CloudFront in the company-account package to avoid global-service / region-restriction risk.
- Avoid high fixed-cost services such as OpenSearch, RDS, EC2, and Bedrock Knowledge Bases.
- Use serverless services: Lambda, Step Functions, S3, DynamoDB, EventBridge Scheduler, Secrets Manager, CloudWatch Logs, and optional API Gateway / Cognito.
- Store Anthropic API key in Secrets Manager.
- Run a quote gate before S3/S4 LLM evaluation.
- Fall back to zero-token rubric mode when the quote exceeds `MAX_RUN_USD`.
- Destroy the landing-validation stacks after validation if the environment is not needed.

## Per-Run Quote

Default quote assumptions:

- Candidate count after S2: 6
- Evaluator model: Claude Sonnet 4.5
- Validator model: Claude Haiku 4.5
- Max per-run budget: USD 0.50
- Estimated AWS fixed allocation: USD 0.01 / run

| Line Item | Model | Estimated Tokens | Price | Estimated Cost |
|---|---|---:|---:|---:|
| S3 Evaluator | Claude Sonnet 4.5 | 9,000 input / 2,400 output | USD 3 / 15 per MTok | USD 0.0630 |
| S4 Validator | Claude Haiku 4.5 | 7,200 input / 1,800 output | USD 1 / 5 per MTok | USD 0.0162 |
| AWS fixed allocation | Lambda / Step Functions / S3 / DynamoDB | - | - | USD 0.0100 |
| **Total** | - | - | - | **USD 0.0892** |

Decision: **approve** because USD 0.0892 <= USD 0.50.

## Estimated Monthly Cost

| Service | Purpose | Estimate |
|---|---|---:|
| S3 | Store pipeline JSON, HTML reports, and quotation files | < USD 1 |
| Lambda | Run S1-S5 pipeline and quote gate | < USD 1 |
| Step Functions | Orchestrate quote-gated workflow | < USD 1 |
| DynamoDB | Store AI / human pick logs | < USD 1 |
| Secrets Manager | Store Anthropic API key | ~ USD 0.40 |
| EventBridge Scheduler | Daily trigger, disabled by default | ~ USD 0 |
| CloudWatch Logs | Execution logs | USD 1-3 |
| API Gateway / Cognito | Optional manual trigger API | < USD 1 |
| Anthropic API | Optional evaluator / validator calls | ~ USD 0.09 per run |

Expected light-use monthly total: **USD 5-15**.

## Excluded Items

These are intentionally out of scope for the USD 100 implementation / landing-validation budget:

- Amazon Bedrock
- Bedrock Knowledge Bases
- CloudFront
- OpenSearch
- RDS
- EC2

## Decision

Proceed with the current CDK architecture. It is designed to stay within USD 100 for company-account landing validation when Anthropic API usage stays within the quote gate.
