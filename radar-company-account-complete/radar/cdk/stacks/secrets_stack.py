"""SecretsStack — Anthropic API key 存 Secrets Manager，Lambda 執行時取用。"""
from aws_cdk import Stack, CfnOutput, SecretValue
from aws_cdk import aws_secretsmanager as sm
from constructs import Construct


class SecretsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *,
                 prefix: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Anthropic API key
        # 首次部署後需手動把真實 key 貼到 Console 或用 aws secretsmanager put-secret-value
        # 這裡建立空 secret，避免真實 key 進 CloudFormation template
        self.anthropic_secret = sm.Secret(
            self, "AnthropicApiKey",
            secret_name=f"{prefix}/anthropic-api-key",
            description="Anthropic API key (sk-ant-...) for tech intel pipeline",
            # 部署時建立空值，後續透過 CLI 更新真實 key
            secret_string_value=SecretValue.unsafe_plain_text("REPLACE_AFTER_DEPLOY"),
        )

        CfnOutput(self, "SecretArn", value=self.anthropic_secret.secret_arn)
        CfnOutput(
            self, "UpdateKeyCommand",
            value=f"aws secretsmanager put-secret-value --secret-id {prefix}/anthropic-api-key --secret-string sk-ant-YOUR_KEY_HERE",
            description="部署後執行此指令更新真實 API key",
        )
