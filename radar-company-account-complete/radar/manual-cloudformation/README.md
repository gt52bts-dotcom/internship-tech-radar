# Pure CloudFormation Deployment

This folder contains a CDK-free CloudFormation path for the company AWS account.
It avoids CDK bootstrap resources such as `CDKToolkit`, `/cdk-bootstrap/.../version`,
and `cdk-hnb659fds-*` roles.

Target Region: `ap-southeast-1` only.

## 1. Build artifacts locally

Run from `radar-company-account-complete/radar/cdk`:

```powershell
$env:PIP_USER = "false"

Remove-Item -Recurse -Force .\layer_build -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force .\layer_build\python | Out-Null
python -m pip install --no-user anthropic feedparser -t .\layer_build\python

Compress-Archive -Path .\layer_build\python -DestinationPath .\lambda-layer.zip -Force
Compress-Archive -Path .\lambda_src\* -DestinationPath .\lambda-code.zip -Force
```

The layer zip must contain this shape:

```text
python/
  anthropic/
  feedparser/
```

## 2. Upload artifacts to S3

Use any existing private S3 bucket in `ap-southeast-1` that the deploying principal
can read from CloudFormation and Lambda.

```powershell
$ARTIFACT_BUCKET = "<existing-artifact-bucket>"

aws s3 cp .\lambda-layer.zip s3://$ARTIFACT_BUCKET/artifacts/cathay-techintel-v3/lambda-layer.zip `
  --profile intern `
  --region ap-southeast-1

aws s3 cp .\lambda-code.zip s3://$ARTIFACT_BUCKET/artifacts/cathay-techintel-v3/lambda-code.zip `
  --profile intern `
  --region ap-southeast-1
```

## 3. Deploy with CloudFormation

If an Anthropic secret already exists, pass its ARN:

```powershell
aws cloudformation deploy `
  --profile intern `
  --region ap-southeast-1 `
  --stack-name cathay-techintel-v3 `
  --template-file ..\manual-cloudformation\cathay-techintel-v3.yaml `
  --capabilities CAPABILITY_NAMED_IAM `
  --parameter-overrides `
    ArtifactBucket=$ARTIFACT_BUCKET `
    ExistingAnthropicSecretArn="arn:aws:secretsmanager:ap-southeast-1:092211181371:secret:cathay-techintel-v3/anthropic-api-key-Lhnx13"
```

If no secret exists, omit `ExistingAnthropicSecretArn`; CloudFormation creates
`cathay-techintel-v3/anthropic-api-key` with a placeholder value. Replace the
secret value in Secrets Manager after deployment. Do not store API keys in Git,
logs, screenshots, or chat.

## 4. Run once

```powershell
$STATE_MACHINE_ARN = aws cloudformation describe-stacks `
  --profile intern `
  --region ap-southeast-1 `
  --stack-name cathay-techintel-v3 `
  --query "Stacks[0].Outputs[?OutputKey=='StateMachineArn'].OutputValue | [0]" `
  --output text

aws stepfunctions start-execution `
  --profile intern `
  --region ap-southeast-1 `
  --state-machine-arn $STATE_MACHINE_ARN `
  --input "{\"run_id\":\"company-cfn-001\"}"
```

## Notes

- This template creates the data bucket, DynamoDB table, IAM roles, Lambda layer,
  seven Lambda functions, Step Functions state machine, log groups, and disabled
  daily scheduler.
- It does not create CloudFront, API Gateway, Cognito, Bedrock, OpenSearch, RDS,
  or EC2.
- If resources with the same names already exist from manual deployment, the stack
  will fail with an already-exists error. Use a different `Prefix`, delete/import
  the existing resources, or deploy in a clean account/Region.
