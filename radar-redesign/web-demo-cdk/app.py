#!/usr/bin/env python3
"""Deploy the artifact-first S1-S5 demo site and its AWS API."""

from pathlib import Path

import aws_cdk as cdk
from aws_cdk import CfnOutput, Duration, RemovalPolicy
from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from constructs import Construct


class RadarWebDemoStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        source_root = Path(__file__).resolve().parents[1]
        web_root = source_root / "web"

        artifacts = s3.Bucket(
            self, "ArtifactBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
            lifecycle_rules=[s3.LifecycleRule(prefix="runs/", expiration=Duration.days(30))],
            removal_policy=RemovalPolicy.RETAIN,
        )
        api_function = lambda_.Function(
            self, "RadarApi",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="web_api.handler.handler",
            code=lambda_.Code.from_asset(str(source_root), exclude=["out", "web-demo-cdk/cdk.out", "tests", "docs", "samples"]),
            timeout=Duration.seconds(120),
            memory_size=1024,
            environment={"ARTIFACT_BUCKET": artifacts.bucket_name},
        )
        api_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject", "s3:GetObject"],
                resources=[artifacts.arn_for_objects("runs/*")],
            )
        )

        api = apigateway.RestApi(
            self, "RadarApiGateway",
            rest_api_name="agentic-cloud-radar-demo",
            deploy_options=apigateway.StageOptions(throttling_burst_limit=5, throttling_rate_limit=2),
            default_cors_preflight_options=apigateway.CorsOptions(allow_origins=apigateway.Cors.ALL_ORIGINS, allow_methods=["GET", "POST", "OPTIONS"]),
        )
        api.root.add_method("ANY", apigateway.LambdaIntegration(api_function))
        proxy = api.root.add_proxy(
            any_method=False,
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=["GET", "POST", "OPTIONS"],
            ),
        )
        proxy.add_method("ANY", apigateway.LambdaIntegration(api_function))

        site = s3.Bucket(
            self, "SiteBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        distribution = cloudfront.Distribution(
            self, "SiteDistribution",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(site),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
        )
        s3deploy.BucketDeployment(
            self, "DeploySite",
            sources=[
                s3deploy.Source.asset(str(web_root)),
                s3deploy.Source.data("config.js", f"window.RADAR_CONFIG = {{ apiBaseUrl: {api.url!r} }};\n"),
            ],
            destination_bucket=site,
            distribution=distribution,
            distribution_paths=["/*"],
        )
        CfnOutput(self, "WebsiteUrl", value=f"https://{distribution.domain_name}")
        CfnOutput(self, "ApiUrl", value=api.url)
        CfnOutput(self, "ArtifactBucketName", value=artifacts.bucket_name)


app = cdk.App()
RadarWebDemoStack(app, "AgenticCloudRadarWebDemo", env=cdk.Environment(region="ap-southeast-1"))
app.synth()
