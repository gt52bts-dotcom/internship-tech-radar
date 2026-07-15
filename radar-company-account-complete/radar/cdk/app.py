#!/usr/bin/env python3
"""Cathay Tech Intel Pipeline v3 · AWS CDK Deployment
用 CDK 部署整套 pipeline 到 AWS，但 AI 呼叫走 api.anthropic.com（非 Bedrock）。

三個 stack：
  1. DataStack     — S3 bucket + DynamoDB table
  2. SecretsStack  — Anthropic API key 存 Secrets Manager
  3. PipelineStack — Lambda × 5 + Step Functions + EventBridge

部署：
  cd cdk
  cdk bootstrap  # 首次
  cdk deploy --all
"""
import aws_cdk as cdk
from stacks.data_stack import DataStack
from stacks.secrets_stack import SecretsStack
from stacks.pipeline_stack import PipelineStack

app = cdk.App()

env = cdk.Environment(region="ap-southeast-1")
prefix = app.node.try_get_context("prefix") or "cathay-techintel-v3"

data_stack = DataStack(app, f"{prefix}-data", env=env, prefix=prefix)
secrets_stack = SecretsStack(app, f"{prefix}-secrets", env=env, prefix=prefix)
pipeline_stack = PipelineStack(
    app, f"{prefix}-pipeline",
    env=env, prefix=prefix,
    bucket=data_stack.bucket,
    table=data_stack.picks_table,
    anthropic_secret=secrets_stack.anthropic_secret,
)
pipeline_stack.add_dependency(data_stack)
pipeline_stack.add_dependency(secrets_stack)

app.synth()
