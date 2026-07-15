"""DataStack: private S3 data/report bucket + DynamoDB pick log.

公司帳戶版（ap-southeast-1 only）：
- 移除 CloudFront：全球服務，控制平面在 us-east-1，SCP 鎖區域會直接擋掉。
  報表改用 S3 presigned URL（s5_report 產生）。
- 移除自建 KMS CMK：改用 S3 managed / AWS managed 加密，少一層權限風險、零額外成本。
- 加 S3 lifecycle：runs/ 底下的中繼 JSON 90 天自動過期（展示 S3 生命週期管理）。
- DynamoDB 加 TTL 欄位 expire_at：pick log 一年後自動清除。
"""
from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as ddb
from aws_cdk import aws_s3 as s3
from constructs import Construct


class DataStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, prefix: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        self.bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name=f"{prefix}-data-{self.account}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,  # 實習結束 cdk destroy 一鍵清空
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="expire-run-artifacts",
                    prefix="runs/",
                    expiration=Duration.days(90),
                ),
            ],
        )

        self.picks_table = ddb.Table(
            self,
            "PicksLogTable",
            table_name=f"{prefix}-picks-log",
            partition_key=ddb.Attribute(name="run_id", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="pick_time", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            encryption=ddb.TableEncryption.AWS_MANAGED,
            time_to_live_attribute="expire_at",
            removal_policy=RemovalPolicy.DESTROY,
        )

        CfnOutput(self, "BucketName", value=self.bucket.bucket_name)
        CfnOutput(self, "PicksTableName", value=self.picks_table.table_name)
